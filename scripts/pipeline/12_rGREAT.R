############################################################
# SUPERGNOVA -> rGREAT enrichment analysis
# Reactome + GO Biological Process
#
# What this script does:
# 1. Reads a whitespace-separated SUPERGNOVA result file
# 2. Filters local covariance windows
# 3. Splits windows by rho direction (positive / negative)
# 4. Converts windows to GRanges
# 5. Runs local rGREAT enrichment
# 6. Extracts enrichment tables with a permissive min_region_hits
# 7. Saves tables and dotplots
# 8. Optionally exports region-gene associations
#
# Notes:
# - This is best interpreted as an exploratory enrichment if your
#   SUPERGNOVA windows are only nominally significant (p_adj < 0.05)
#   and not FDR-significant.
# - We analyze positive and negative rho separately.
############################################################


suppressPackageStartupMessages({
  library(data.table)
  library(dplyr)
  library(GenomicRanges)
  library(IRanges)
  library(rGREAT)
  library(ggplot2)
  library(yaml)
})

############################################################
# PARAMETERS & INPUTS
############################################################

# Genome / TSS source
genome_build <- "hg19"

# Filtering parameters for SUPERGNOVA windows
padj_cutoff <- 0.05
min_snps <- 100
drop_na_rho <- TRUE

# GREAT parameters
min_region_hits <- 1      # important for small region sets
min_gene_set_size <- 5    # exclude very tiny gene sets
cores_to_use <- 1

# Plot parameters
top_n_terms <- 15


############################################################
# CLI ARGUMENTS
############################################################

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  
  get_arg <- function(flag) {
    idx <- which(args == flag)
    if (length(idx) == 0 || idx == length(args)) return(NULL)
    args[idx + 1]
  }
  
  file_arg <- get_arg("--file")
  env_arg  <- get_arg("--env")
  
  if (is.null(file_arg)) stop("Missing --file")
  if (is.null(env_arg)) stop("Missing --env")
  if (!(env_arg %in% c("local", "remote"))) {
    stop("--env must be 'local' or 'remote'")
  }
  
  list(
    file = file_arg,
    env  = env_arg
  )
}


############################################################
# CONFIG HELPERS
############################################################

get_config_file <- function(env) {
  if (env == "local") {
    return("/home/maria/git/SOROLLA/config/config.yaml")
  } else {
    return("/gpfs/projects/bsc02/mflores/gencor/config/config.yaml")
  }
}

load_config_file <- function(config_file) {
  if (!file.exists(config_file)) {
    stop("Configuration file not found: ", config_file)
  }
  
  config <- tryCatch(
    yaml::read_yaml(config_file),
    error = function(e) {
      stop("Invalid YAML configuration: ", conditionMessage(e))
    }
  )
  
  return(config)
}

trim_slashes <- function(x) {
  gsub("^/+|/+$", "", x)
}

join_config_path <- function(base_path, ...) {
  parts <- c(...)
  parts <- parts[!is.na(parts) & nzchar(parts)]
  
  cleaned_parts <- vapply(parts, trim_slashes, character(1))
  
  do.call(file.path, as.list(c(base_path, cleaned_parts)))
}


############################################################
# FILE NAME PARSING
############################################################

get_analysis_name_from_file <- function(file_name) {
  file_base <- basename(file_name)
  file_base <- tools::file_path_sans_ext(file_base)
  
  parts <- strsplit(file_base, "_", fixed = TRUE)[[1]]
  
  if (length(parts) != 4) {
    stop(
      "Input file name must follow the format: id1_label1_id2_label2\n",
      "Received: ", file_name
    )
  }
  
  analysis_name <- paste(parts[2], parts[4], sep = "_")
  return(analysis_name)
}


############################################################
# BUILD INPUT / OUTPUT PATHS FROM CONFIG
############################################################

build_paths_from_config <- function(file_name, env, config) {
  base_path <- config[[env]]$base_path
  
  if (is.null(base_path)) {
    stop("Could not find base_path for env = ", env, " in config file.")
  }
  
  analysis_name <- get_analysis_name_from_file(file_name)
  
  input_file <- join_config_path(
    base_path,
    config$Results$results_folder,
    config$Results$folder_supergnova,
    file_name
  )
  
  output_dir <- join_config_path(
    base_path,
    config$Results$results_folder,
    config$Results$RGreat,
    analysis_name
  )
  
  list(
    input_file = input_file,
    output_dir = output_dir,
    analysis_name = analysis_name
  )
}


############################################################
# 1) READ SUPERGNOVA OUTPUT
# - SUPERGNOVA results are whitespace-delimited files
############################################################
read_supergnova <- function(file) {
  message("Reading file: ", file)
  
  df <- data.table::fread(file, header = TRUE, data.table = FALSE)
  
  # Fallback if fread collapses columns
  if (ncol(df) == 1) {
    df <- read.table(file, header = TRUE, stringsAsFactors = FALSE)
  }
  
  required_cols <- c("chr", "start", "end", "rho", "corr", "h2_1", "h2_2", "var", "p", "m")
  missing_cols <- setdiff(required_cols, colnames(df))
  
  if (length(missing_cols) > 0) {
    stop("Missing expected columns: ", paste(missing_cols, collapse = ", "))
  }
  
  df <- df %>%
    dplyr::mutate(
      chr = as.character(chr),
      chr = ifelse(grepl("^chr", chr), chr, paste0("chr", chr)),
      start = as.integer(start),
      end = as.integer(end),
      rho = as.numeric(rho),
      corr = as.numeric(corr),
      h2_1 = as.numeric(h2_1),
      h2_2 = as.numeric(h2_2),
      var = as.numeric(var),
      p = as.numeric(p),
      m = as.integer(m),
      padj = p.adjust(p, method = "BH"),
      direction = dplyr::case_when(
        rho > 0 ~ "positive",
        rho < 0 ~ "negative",
        TRUE ~ "zero"
      )
    )
  
  message("Successfully read file. Rows: ", nrow(df), " | Cols: ", ncol(df))
  return(df)
}


############################################################
# 2) FILTER SUPERGNOVA WINDOWS
############################################################
filter_supergnova_windows <- function(df,
                                      padj_cutoff = 0.05,
                                      min_snps = 100,
                                      drop_na_rho = TRUE) {
  message("Filtering by p-value. Rows before filtering: ", nrow(df))
  
  out <- df %>% dplyr::filter(padj < padj_cutoff, m >= min_snps)
  
  message("Filtering by p-value. Rows after filtering: ", nrow(out))
  
  if (drop_na_rho) {
    message("Filtering missing rho. Rows before filtering: ", nrow(out))
    out <- out %>% dplyr::filter(!is.na(rho))
    message("Filtering missing rho. Rows after filtering: ", nrow(out))
  }
  
  return(out)
}


############################################################
# 3) CONVERT TO GRanges
############################################################
supergnova_to_granges <- function(df,
                                  reduce_overlaps = FALSE,
                                  keep_metadata = TRUE) {
  
  message("Converting to GRanges")
  
  gr <- GRanges(
    seqnames = df$chr,
    ranges = IRanges(start = df$start + 1, end = df$end)
  )
  # +1 because SUPERGNOVA-like is partitioned with a BED file, usually 0-based
  # 0-based = start inclusive, end exclusive
  # GRanges uses 1-based coordinates
  
  if (keep_metadata) {
    mcols(gr) <- df[, setdiff(colnames(df), c("chr", "start", "end")), drop = FALSE]
  }
  
  # Normally SUPERGNOVA blocks are already non-overlapping,
  # keep reduce_overlaps = FALSE unless there's a reason to merge them
  if (reduce_overlaps) {
    gr <- reduce(gr, with.revmap = FALSE)
  }
  

  message("Converted successfully to GRanges.")
  return(gr)
}


############################################################
# 4) RUN rGREAT
############################################################
run_rgreat_from_supergnova <- function(gr,
                                       gene_sets,
                                       tss_source = "hg19",
                                       min_gene_set_size = 5,
                                       cores = 1) {
  message("Running rGREAT with gene set collection: ", gene_sets)
  
  great_obj <- rGREAT::great(
    gr = gr,
    gene_sets = gene_sets,
    tss_source = tss_source,
    min_gene_set_size = min_gene_set_size,
    cores = cores
  )
  
  message("rGREAT finished. Returned object class: ",
          paste(class(great_obj), collapse = ", "))
  
  return(great_obj)
}


############################################################
# 5) EXTRACT ENRICHMENT TABLE
############################################################
extract_rgreat_table <- function(great_obj, min_region_hits = 1) {
  message("Creating enrichment table from rGREAT")
  tb <- getEnrichmentTable(great_obj, min_region_hits = min_region_hits)
  
  if (is.null(tb) || nrow(tb) == 0) {
    return(tb)
  }
  
  # Use description if present, otherwise fall back to ID
  if (!"description" %in% colnames(tb)) {
    tb$description <- tb$id
  }
  
  tb <- tb %>%
    dplyr::mutate(
      term = description,
      minus_log10_fdr = -log10(pmax(p_adjust, .Machine$double.xmin))
    ) %>%
    dplyr::arrange(p_adjust, desc(fold_enrichment))
  
  message("Enrichment table created. Columns: ",
          paste(colnames(tb), collapse = ", "))
  
  return(tb)
}


############################################################
# 6) FORMAT TERM LABELS FOR PLOTS
############################################################
format_term_labels <- function(x,
                               wrap_width = 45,
                               remove_prefix = TRUE,
                               shorten_labels = FALSE,
                               max_chars = 100) {
  
  x2 <- x
  
  # Remove common database prefixes
  if (remove_prefix) {
    x2 <- gsub("^REACTOME_", "", x2)
    x2 <- gsub("^HALLMARK_", "", x2)
    x2 <- gsub("^GO_", "", x2)
  }
  
  # Replace underscores with spaces
  x2 <- gsub("_", " ", x2)
  
  # Convert to Title Case
  x2 <- tools::toTitleCase(tolower(x2))
  
  # Optionally shorten very long labels
  if (shorten_labels) {
    x2 <- ifelse(
      nchar(x2) > max_chars,
      paste0(substr(x2, 1, max_chars), "..."),
      x2
    )
  }
  
  # Wrap text across multiple lines
  x2 <- vapply(
    x2,
    function(xx) paste(strwrap(xx, width = wrap_width), collapse = "\n"),
    character(1)
  )
  
  return(x2)
}


############################################################
# 7) ENRICHMENT DOTPLOT
############################################################
plot_rgreat_dotplot <- function(tb,
                                top_n = 15,
                                title = "rGREAT enrichment",
                                wrap_width = 45,
                                shorten_labels = FALSE,
                                max_chars = 100) {
  if (is.null(tb) || nrow(tb) == 0) {
    message("No enriched terms to plot for: ", title)
    return(invisible(NULL))
  }
  
  # Safety fallback in case tb comes without derived columns
  if (!"term" %in% colnames(tb)) {
    if ("description" %in% colnames(tb)) {
      tb$term <- tb$description
    } else if ("id" %in% colnames(tb)) {
      tb$term <- tb$id
    } else {
      stop("Input enrichment table has neither 'term', 'description', nor 'id'.")
    }
  }
  
  if (!"minus_log10_fdr" %in% colnames(tb)) {
    if ("p_adjust" %in% colnames(tb)) {
      tb$minus_log10_fdr <- -log10(pmax(tb$p_adjust, .Machine$double.xmin))
    } else {
      stop("Input enrichment table does not contain 'minus_log10_fdr' or 'p_adjust'.")
    }
  }
  
  message("Creating dotplot for ", nrow(tb), " enriched terms")
  
  plot_df <- tb %>%
    dplyr::slice_head(n = top_n) %>%
    dplyr::mutate(
      term_plot = format_term_labels(
        term,
        wrap_width = wrap_width,
        shorten_labels = shorten_labels,
        max_chars = max_chars
      ),
      term_plot = factor(term_plot, levels = rev(term_plot))
    )
  
  dotplot <- ggplot(
    plot_df,
    aes(
      x = fold_enrichment,
      y = term_plot,
      size = observed_region_hits,
      color = minus_log10_fdr
    )
  ) +
    geom_point() +
    labs(
      title = title,
      x = "Fold enrichment",
      y = NULL,
      color = expression(-log[10](FDR)),
      size = "Region hits"
    ) +
    theme_bw(base_size = 12) +
    theme(
      axis.text.y = element_text(size = 10, lineheight = 0.95),
      plot.title = element_text(hjust = 0.5, face = "bold"),
      plot.margin = margin(10, 20, 10, 20)
    )
  
  return(dotplot)
}


############################################################
# 8) SAVE TABLES AND PLOTS
############################################################
save_rgreat_results <- function(tb,
                                plot_obj,
                                output_prefix,
                                output_dir,
                                plot_width = 12,
                                plot_height = 8) {
  
  message("Saving table ", output_prefix, " at: ", output_dir)
  
  if (!is.null(tb) && nrow(tb) > 0) {
    fwrite(
      tb,
      file.path(output_dir, paste0(output_prefix, "_table.tsv")),
      sep = "\t"
    )
  }
  
  message("Saving plot as pdf and png ", output_prefix, " at: ", output_dir)
  
  if (!is.null(plot_obj)) {
    ggsave(
      filename = file.path(output_dir, paste0(output_prefix, "_dotplot.pdf")),
      plot = plot_obj,
      width = plot_width,
      height = plot_height
    )
    
    ggsave(
      filename = file.path(output_dir, paste0(output_prefix, "_dotplot.png")),
      plot = plot_obj,
      width = plot_width,
      height = plot_height,
      dpi = 300
    )
  }
}


############################################################
# 9) SAVE REGION-GENE ASSOCIATIONS
############################################################
save_region_gene_associations <- function(great_obj,
                                          output_prefix,
                                          output_dir) {
  assoc <- getRegionGeneAssociations(great_obj)
  
  # Convert to data.frame if possible
  assoc_df <- as.data.frame(assoc)
  
  fwrite(
    assoc_df,
    file.path(output_dir, paste0(output_prefix, "_region_gene_associations.tsv")),
    sep = "\t"
  )
  
  message(
    "Saved associations at: ",
    file.path(output_dir, paste0(output_prefix, "_region_gene_associations.tsv"))
  )
  
  return(assoc_df)
}


############################################################
# 10) VOLCANO PLOT
############################################################
# save_rgreat_volcano <- function(great_obj,
#                                 output_prefix,
#                                 output_dir,
#                                 plot_width = 8,
#                                 plot_height = 6) {
#   
#   message("Saving volcano plot: ", output_prefix)
#   
#   pdf(
#     file.path(output_dir, paste0(output_prefix, "_volcano.pdf")),
#     width = plot_width,
#     height = plot_height
#   )
#   
#   try(plotVolcano(great_obj), silent = TRUE)
#   dev.off()
#   
#   png(
#     file.path(output_dir, paste0(output_prefix, "_volcano.png")),
#     width = plot_width,
#     height = plot_height,
#     units = "in",
#     res = 300
#   )
#   
#   try(plotVolcano(great_obj), silent = TRUE)
#   dev.off()
# }


############################################################
# 11) REGION–GENE ASSOCIATION PLOT
############################################################
save_region_gene_plot <- function(great_obj,
                                  output_prefix,
                                  output_dir,
                                  plot_width = 10,
                                  plot_height = 6) {
  
  message("Saving region-gene association plot: ", output_prefix)
  
  pdf(
    file.path(output_dir, paste0(output_prefix, "_region_gene_plot.pdf")),
    width = plot_width,
    height = plot_height
  )
  
  try(plotRegionGeneAssociations(great_obj), silent = TRUE)
  dev.off()
  
  png(
    file.path(output_dir, paste0(output_prefix, "_region_gene_plot.png")),
    width = plot_width,
    height = plot_height,
    units = "in",
    res = 300
  )
  
  try(plotRegionGeneAssociations(great_obj), silent = TRUE)
  dev.off()
}


############################################################
# 12) MAIN WRAPPER
############################################################
analyze_supergnova_rgreat <- function(file,
                                      analysis_name,
                                      output_dir,
                                      gene_sets = c("msigdb:H",
                                                    "msigdb:C2:CP:REACTOME",
                                                    "GO:BP"),
                                      genome = "hg19",
                                      padj_cutoff = 0.05,
                                      min_snps = 100,
                                      drop_na_rho = TRUE,
                                      run_positive = TRUE,
                                      run_negative = TRUE,
                                      run_all = TRUE,
                                      reduce_overlaps = FALSE,
                                      min_region_hits = 1,
                                      min_gene_set_size = 5,
                                      cores = 1,
                                      top_n_terms = 15,
                                      wrap_width = 45,
                                      shorten_labels = FALSE,
                                      max_chars = 100,
                                      plot_width = 12,
                                      plot_height = 8) {
  
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  
  ##########################################################
  # READ + FILTER
  ##########################################################
  
  df <- read_supergnova(file)
  
  df_filt <- filter_supergnova_windows(
    df,
    padj_cutoff = padj_cutoff,
    min_snps = min_snps,
    drop_na_rho = drop_na_rho
  )
  
  if (nrow(df_filt) == 0) {
    message("No significant regions found for: ", analysis_name)
    return(NULL)
  }
  
  fwrite(
    df_filt,
    file.path(output_dir, paste0(analysis_name, "_filtered_windows.tsv")),
    sep = "\t"
  )
  
  ##########################################################
  # DEFINE GROUPS
  ##########################################################
  
  groups_to_run <- list()
  
  if (run_positive) {
    groups_to_run$positive <- df_filt %>% filter(direction == "positive")
  }
  
  if (run_negative) {
    groups_to_run$negative <- df_filt %>% filter(direction == "negative")
  }
  
  if (run_all) {
    groups_to_run$all <- df_filt
  }
  
  ##########################################################
  # RUN ANALYSIS
  ##########################################################
  
  results <- list()
  
  for (gs in gene_sets) {
    
    gene_set_label <- gsub("[: ]", "_", gs)
    gene_set_label <- gsub("[^A-Za-z0-9_]", "_", gene_set_label)
    
    sub_output_dir <- file.path(output_dir, gene_set_label)
    dir.create(sub_output_dir, recursive = TRUE, showWarnings = FALSE)
    
    results[[gene_set_label]] <- list()
    
    for (group_name in names(groups_to_run)) {
      
      subdf <- groups_to_run[[group_name]]
      
      if (nrow(subdf) == 0) next
      
      message("Running ", analysis_name,
              " | ", gs,
              " | ", group_name,
              " (", nrow(subdf), " windows)")
      
      gr <- supergnova_to_granges(
        subdf,
        reduce_overlaps = reduce_overlaps,
        keep_metadata = TRUE
      )
      
      great_obj <- run_rgreat_from_supergnova(
        gr = gr,
        gene_sets = gs,
        tss_source = genome,
        min_gene_set_size = min_gene_set_size,
        cores = cores
      )
      
      tb <- extract_rgreat_table(
        great_obj,
        min_region_hits = min_region_hits
      )
      
      plot_title <- paste0(analysis_name, " - ", group_name)
      
      dotplot <- plot_rgreat_dotplot(
        tb,
        top_n = top_n_terms,
        title = plot_title,
        wrap_width = wrap_width,
        shorten_labels = shorten_labels,
        max_chars = max_chars
      )
      
      output_prefix <- paste0(analysis_name, "_", group_name)
      
      save_rgreat_results(
        tb,
        dotplot,
        output_prefix,
        sub_output_dir,
        plot_width,
        plot_height
      )
      
      assoc_df <- save_region_gene_associations(
        great_obj,
        output_prefix,
        sub_output_dir
      )
      
      # save_rgreat_volcano(
      #   great_obj,
      #   output_prefix,
      #   sub_output_dir
      # )
      # 
      save_region_gene_plot(
        great_obj,
        output_prefix,
        sub_output_dir
      )
      
      results[[gene_set_label]][[group_name]] <- list(
        table = tb,
        associations = assoc_df,
        plot = dotplot
      )
    }
  }
  
  return(results)
}


############################################################
# 13) MAIN
############################################################
# CHANGED:
# - Replaces the old hardcoded test block
# - Builds paths automatically from config
# - Runs from terminal with --file and --env

main <- function() {
  args <- parse_args()
  
  config_file <- get_config_file(args$env)
  message("Using config file: ", config_file)
  
  config <- load_config_file(config_file)
  
  built_paths <- build_paths_from_config(
    file_name = args$file,
    env = args$env,
    config = config
  )
  
  input_file <- built_paths$input_file
  output_dir <- built_paths$output_dir
  analysis_name <- built_paths$analysis_name
  
  message("Input SUPERGNOVA file: ", input_file)
  message("Analysis name: ", analysis_name)
  message("Output directory: ", output_dir)
  
  # CHANGED: explicit file existence check before analysis
  if (!file.exists(input_file)) {
    stop("SUPERGNOVA input file not found: ", input_file)
  }
  
  analyze_supergnova_rgreat(
    file = input_file,
    analysis_name = analysis_name,
    output_dir = output_dir,
    gene_sets = c("msigdb:H", "msigdb:C2:CP:REACTOME", "GO:BP"),
    genome = genome_build,
    padj_cutoff = padj_cutoff,
    min_snps = min_snps,
    drop_na_rho = drop_na_rho,
    run_positive = TRUE,
    run_negative = TRUE,
    run_all = TRUE,
    reduce_overlaps = FALSE,
    min_region_hits = min_region_hits,
    min_gene_set_size = min_gene_set_size,
    cores = cores_to_use,
    top_n_terms = top_n_terms,
    wrap_width = 40,
    shorten_labels = FALSE,
    max_chars = 100,
    plot_width = 13,
    plot_height = 8
  )
  
  message("Analysis finished successfully.")
}

main()