library(dplyr)
library(readr)
library(data.table)
library(tidyverse)
# install.packages("metafor")
library(metafor)
# install.packages("clubSandwich")
library(clubSandwich)

# Set env & variables
setwd("~/git/SOROLLA/")
wd <- getwd()
results_folder <- "/Results/"
metaanalisis_folder <- "Meta/"
results_path <- paste0(wd, results_folder)
metaanalisis_save <- paste0(results_path, metaanalisis_folder)

# Load results
ldsc <- fread(paste0(results_path,"ldsc_genetic_correlation_pcorrected.csv"), stringsAsFactors = F,sep=",")
hdl <- fread(paste0(results_path, "hdl_genetic_correlation_pcorrected.csv"), stringsAsFactors = F,sep=",")

# Create disease pairs for processing
## LDSC
ldsc_no_self_pairs <- ldsc[ldsc$disease_1 != ldsc$disease_2,]
unique_pairs_df <- data.frame(
  d1 = pmin(ldsc_no_self_pairs$disease_1, ldsc_no_self_pairs$disease_2),
  d2 = pmax(ldsc_no_self_pairs$disease_1, ldsc_no_self_pairs$disease_2),
  stringsAsFactors = FALSE
)
ldsc_unique_pairs <- unique(unique_pairs_df)
ldsc_unique_pairs <- ldsc_unique_pairs[order(ldsc_unique_pairs$d1, ldsc_unique_pairs$d2), ]


## HDL (has less pairs than LDSC so we need to process it differently)
hdl_no_self_pairs <- hdl[hdl$disease_1 != hdl$disease_2,]
unique_pairs_df <- data.frame(
  d1 = pmin(hdl_no_self_pairs$disease_1, hdl_no_self_pairs$disease_2),
  d2 = pmax(hdl_no_self_pairs$disease_1, hdl_no_self_pairs$disease_2),
  stringsAsFactors = FALSE
)
hdl_unique_pairs <- unique(unique_pairs_df)
hdl_unique_pairs <- hdl_unique_pairs[order(hdl_unique_pairs$d1, hdl_unique_pairs$d2), ]


# Meta-analysis function with metafor
metafor_process <- function(software_df,
                            software_name,
                            d1,
                            d2,
                            just_main_minor = TRUE,
                            output_folder,
                            mv_min_k = 5,
                            robust_min_clusters_uni = 2,
                            robust_min_clusters_mv  = 4) {
  
  stopifnot(is.logical(just_main_minor))
  
  # ---------------------------------------------------------------------------
  # Why we convert to data.table:
  # The function uses data.table subsetting with ..cols syntax. If the input is a
  # data.frame, that would fail. Converting here makes the behavior consistent.
  # ---------------------------------------------------------------------------
  input_dt <- data.table::as.data.table(software_df)
  
  analysis_mode_label <- if (just_main_minor) "Main_Minor" else "All"
  
  # ---------------------------------------------------------------------------
  # 1) Subset to the disease pair (in either direction)
  # We keep both orientations, and later we force the order to be (d1, d2).
  # ---------------------------------------------------------------------------
  pair_dt <- input_dt[
    (disease_1 == d1 & disease_2 == d2) |
      (disease_1 == d2 & disease_2 == d1)
  ]
  message("Rows after disease filter: ", nrow(pair_dt))
  
  # ---------------------------------------------------------------------------
  # 2) Apply selection filter (Main/Minor only or all)
  # ---------------------------------------------------------------------------
  if (just_main_minor) {
    message("Selected only main and minor datasets.")
    pair_dt <- pair_dt[selection_1 %in% c("main", "minor") & selection_2 %in% c("main", "minor")]
  } else {
    message("Selected all datasets (including subtypes).")
  }
  message("Rows after selection filter: ", nrow(pair_dt))
  
  # ---------------------------------------------------------------------------
  # 3) Prepare output folder + results CSV with an "upsert" strategy
  # We overwrite the row for the same (software, disease_1, disease_2, analysis_mode),
  # avoiding duplicates when re-running the pipeline.
  # ---------------------------------------------------------------------------
  if (!dir.exists(output_folder)) dir.create(output_folder, recursive = TRUE)
  results_csv_path <- file.path(output_folder, paste0("0_", software_name, "_meta_results.csv"))
  
  upsert_csv <- function(path, row_df) {
    if (file.exists(path)) {
      old_data <- read.csv(path, stringsAsFactors = FALSE)
      
      # Backward compatibility if the CSV was created before adding analysis_mode
      if (!"analysis_mode" %in% colnames(old_data)) old_data$analysis_mode <- "Unknown"
      
      # Add missing columns on either side to allow row-binding safely
      for (nm in setdiff(names(row_df), names(old_data))) old_data[[nm]] <- NA
      for (nm in setdiff(names(old_data), names(row_df))) row_df[[nm]] <- NA
      
      old_data <- old_data[!(
        old_data$software       == row_df$software[1] &
          old_data$disease_1    == row_df$disease_1[1] &
          old_data$disease_2    == row_df$disease_2[1] &
          old_data$analysis_mode == row_df$analysis_mode[1]
      ), ]
      
      out_to_write <- rbind(old_data, row_df)
      write.csv(out_to_write, path, row.names = FALSE)
    } else {
      write.csv(row_df, path, row.names = FALSE)
    }
  }
  
  # ---------------------------------------------------------------------------
  # Small helpers to keep character columns clean and avoid empty strings behaving
  # like valid cluster IDs.
  # ---------------------------------------------------------------------------
  clean_chr <- function(x) {
    x <- as.character(x)
    x[x == ""] <- NA
    x
  }
  
  # ---------------------------------------------------------------------------
  # 4) If empty after filters, return a standardized row (no analysis possible).
  # ---------------------------------------------------------------------------
  if (nrow(pair_dt) == 0) {
    out_empty <- data.frame(
      software = software_name,
      analysis_mode = analysis_mode_label,
      model_used = "NONE",
      decision_reason = "No rows after filters",
      robust_used_side = NA_character_,
      robust_decision_reason = NA_character_,
      
      disease_1 = d1,
      disease_2 = d2,
      
      k_raw = 0,
      k = 0,
      
      rg_res = NA_real_, se_res = NA_real_, zval_res = NA_real_, pval_res = NA_real_,
      ci_lb_res = NA_real_, ci_ub_res = NA_real_,
      het_res = NA_real_, pval_het_res = NA_real_,
      
      rg_rob1 = NA_real_, se_rob1 = NA_real_, t_rob1 = NA_real_, df_rob1 = NA_real_, p_rob1 = NA_real_,
      ci_lb_rob1 = NA_real_, ci_ub_rob1 = NA_real_,
      rg_rob2 = NA_real_, se_rob2 = NA_real_, t_rob2 = NA_real_, df_rob2 = NA_real_, p_rob2 = NA_real_,
      ci_lb_rob2 = NA_real_, ci_ub_rob2 = NA_real_,
      
      n_clusters_id1 = NA_integer_, n_clusters_id2 = NA_integer_,
      stringsAsFactors = FALSE
    )
    upsert_csv(results_csv_path, out_empty)
    return(out_empty)
  }
  
  # ---------------------------------------------------------------------------
  # 5) Select the columns needed downstream
  # We keep this flexible: only columns that exist are selected.
  # ---------------------------------------------------------------------------
  requested_cols <- c(
    "disease_1", "disease_subtype_1", "disease_2", "disease_subtype_2",
    "selection_1", "id_1", "selection_2", "id_2", "label_1", "label_2",
    "Nca_val_1", "N_num_1", "Nca_val_2", "N_num_2",
    "rg", "se", "p", "p_corrected_FDR", "p_FDR_rejected"
  )
  available_cols <- requested_cols[requested_cols %in% colnames(pair_dt)]
  meta_input_dt <- pair_dt[, ..available_cols]
  
  # k_raw counts rows after filters, before dropping missing/invalid rg/se
  k_raw <- nrow(meta_input_dt)
  
  # ---------------------------------------------------------------------------
  # 6) Force the ordering to always be (d1, d2)
  # This prevents accidental swapping when input rows come as (d2, d1).
  # ---------------------------------------------------------------------------
  need_swap <- (meta_input_dt$disease_1 == d2 & meta_input_dt$disease_2 == d1)
  
  swap_cols <- function(left, right) {
    if (left %in% names(meta_input_dt) && right %in% names(meta_input_dt)) {
      tmp <- meta_input_dt[need_swap, get(left)]
      meta_input_dt[need_swap, (left) := meta_input_dt[need_swap, get(right)]]
      meta_input_dt[need_swap, (right) := tmp]
    }
  }
  
  if (any(need_swap, na.rm = TRUE)) {
    swap_cols("disease_1", "disease_2")
    swap_cols("disease_subtype_1", "disease_subtype_2")
    swap_cols("selection_1", "selection_2")
    swap_cols("id_1", "id_2")
    swap_cols("label_1", "label_2")
    swap_cols("Nca_val_1", "Nca_val_2")
    swap_cols("N_num_1", "N_num_2")
  }
  
  # ---------------------------------------------------------------------------
  # 7) Validate required columns for modeling
  # ---------------------------------------------------------------------------
  required_cols <- c("rg", "se", "p", "id_1", "id_2", "selection_1", "selection_2")
  if (!all(required_cols %in% colnames(meta_input_dt))) {
    
    out_fail <- data.frame(
      software = software_name,
      analysis_mode = analysis_mode_label,
      model_used = "NONE",
      decision_reason = "Missing required columns (rg/se/p/id_1/id_2/selection_1/selection_2)",
      robust_used_side = NA_character_,
      robust_decision_reason = NA_character_,
      
      disease_1 = d1, disease_2 = d2,
      k_raw = k_raw,
      k = NA_integer_,
      
      rg_res = NA_real_, se_res = NA_real_, zval_res = NA_real_, pval_res = NA_real_,
      ci_lb_res = NA_real_, ci_ub_res = NA_real_,
      het_res = NA_real_, pval_het_res = NA_real_,
      
      rg_rob1 = NA_real_, se_rob1 = NA_real_, t_rob1 = NA_real_, df_rob1 = NA_real_, p_rob1 = NA_real_,
      ci_lb_rob1 = NA_real_, ci_ub_rob1 = NA_real_,
      rg_rob2 = NA_real_, se_rob2 = NA_real_, t_rob2 = NA_real_, df_rob2 = NA_real_, p_rob2 = NA_real_,
      ci_lb_rob2 = NA_real_, ci_ub_rob2 = NA_real_,
      
      n_clusters_id1 = NA_integer_, n_clusters_id2 = NA_integer_,
      stringsAsFactors = FALSE
    )
    upsert_csv(results_csv_path, out_fail)
    return(out_fail)
  }
  
  # ---------------------------------------------------------------------------
  # 8) Create a stable plot order
  # This makes forest plots visually consistent across runs.
  # ---------------------------------------------------------------------------
  selection_pair_key <- paste0(meta_input_dt$selection_1, "|", meta_input_dt$selection_2)
  
  ordered_keys <- c(
    "main|main",
    "main|minor",
    "minor|main",
    "minor|minor",
    "main|subtype",
    "minor|subtype",
    "main|subtype-family",
    "minor|subtype-family",
    "subtype|main",
    "subtype|minor",
    "subtype-family|main",
    "subtype-family|minor"
  )
  
  meta_input_dt[, plot_order_rank := match(selection_pair_key, ordered_keys)]
  meta_input_dt[is.na(plot_order_rank), plot_order_rank := 13L]
  data.table::setorder(meta_input_dt, plot_order_rank)
  
  meta_input_dt[, sig_star := ifelse(!is.na(p_FDR_rejected) & p_FDR_rejected, "*", "")]
  
  # ---------------------------------------------------------------------------
  # 9) Build the modeling dataset: keep only complete/valid rg and se
  # We require finite, positive SE to avoid invalid variances.
  # ---------------------------------------------------------------------------
  meta_input_dt[, id_1 := clean_chr(id_1)]
  meta_input_dt[, id_2 := clean_chr(id_2)]
  
  meta_model_dt <- meta_input_dt[!is.na(rg) & !is.na(se) & is.finite(se) & se > 0]
  k_complete <- nrow(meta_model_dt)
  
  if (k_complete == 0) {
    out_fail <- data.frame(
      software = software_name,
      analysis_mode = analysis_mode_label,
      model_used = "NONE",
      decision_reason = "No complete cases (rg/se missing or invalid)",
      robust_used_side = NA_character_,
      robust_decision_reason = NA_character_,
      
      disease_1 = d1, disease_2 = d2,
      k_raw = k_raw,
      k = 0,
      
      rg_res = NA_real_, se_res = NA_real_, zval_res = NA_real_, pval_res = NA_real_,
      ci_lb_res = NA_real_, ci_ub_res = NA_real_,
      het_res = NA_real_, pval_het_res = NA_real_,
      
      rg_rob1 = NA_real_, se_rob1 = NA_real_, t_rob1 = NA_real_, df_rob1 = NA_real_, p_rob1 = NA_real_,
      ci_lb_rob1 = NA_real_, ci_ub_rob1 = NA_real_,
      rg_rob2 = NA_real_, se_rob2 = NA_real_, t_rob2 = NA_real_, df_rob2 = NA_real_, p_rob2 = NA_real_,
      ci_lb_rob2 = NA_real_, ci_ub_rob2 = NA_real_,
      
      n_clusters_id1 = NA_integer_, n_clusters_id2 = NA_integer_,
      stringsAsFactors = FALSE
    )
    upsert_csv(results_csv_path, out_fail)
    return(out_fail)
  }
  
  n_clusters_id1 <- meta_model_dt[, data.table::uniqueN(na.omit(id_1))]
  n_clusters_id2 <- meta_model_dt[, data.table::uniqueN(na.omit(id_2))]
  
  # ---------------------------------------------------------------------------
  # 10) Detect nesting/confounding between id_1 and id_2
  # Why:
  # If each id_1 maps to exactly one id_2 (or vice versa), random effects
  # (~1|id_1 + ~1|id_2) become non-identifiable / redundant. This is a common source
  # of failures (and also a frequent reason robust clustering errors happen).
  # ---------------------------------------------------------------------------
  id2_per_id1 <- meta_model_dt[, .(n_id2 = data.table::uniqueN(id_2)), by = id_1]
  id1_per_id2 <- meta_model_dt[, .(n_id1 = data.table::uniqueN(id_1)), by = id_2]
  
  all_id1_maps_to_single_id2 <- all(id2_per_id1$n_id2 == 1)
  all_id2_maps_to_single_id1 <- all(id1_per_id2$n_id1 == 1)
  
  nested_or_confounded <- all_id1_maps_to_single_id2 || all_id2_maps_to_single_id1
  
  # ---------------------------------------------------------------------------
  # 11) Decide model: NONE (k=1), UNI, or MV
  # We only use MV if:
  # - enough studies (k >= mv_min_k)
  # - at least 2 clusters on each side
  # - AND the design is not nested/confounded between id_1 and id_2
  # ---------------------------------------------------------------------------
  model_used <- "NONE"
  decision_reason <- ""
  fitted_model <- NULL
  model_for_plot <- NULL
  
  # Output defaults
  pooled_estimate <- NA_real_
  pooled_se <- NA_real_
  pooled_stat <- NA_real_
  pooled_p <- NA_real_
  pooled_ci_lb <- NA_real_
  pooled_ci_ub <- NA_real_
  heterogeneity_QE <- NA_real_
  heterogeneity_QEp <- NA_real_
  
  if (k_complete == 1) {
    
    model_used <- "NONE"
    decision_reason <- "Single dataset (no meta-analysis). Forest plot uses a fixed-effect placeholder."
    
    model_for_plot <- tryCatch(
      metafor::rma.uni(yi = meta_model_dt$rg, vi = meta_model_dt$se^2, method = "FE"),
      error = function(e) NULL
    )
    
    pooled_estimate <- as.numeric(meta_model_dt$rg[1])
    pooled_se <- as.numeric(meta_model_dt$se[1])
    
    pooled_stat <- if (!is.na(pooled_se) && pooled_se > 0) pooled_estimate / pooled_se else NA_real_
    pooled_p <- as.numeric(meta_model_dt$p[1])
    
    pooled_ci_lb <- pooled_estimate - 1.96 * pooled_se
    pooled_ci_ub <- pooled_estimate + 1.96 * pooled_se
    
    heterogeneity_QE  <- NA_real_
    heterogeneity_QEp <- NA_real_
    
  } else {
    
    mv_is_allowed <- (k_complete >= mv_min_k) &&
      (n_clusters_id1 >= 2) &&
      (n_clusters_id2 >= 2) &&
      !nested_or_confounded
    
    if (mv_is_allowed) {
      
      model_used <- "MV"
      decision_reason <- paste0(
        "MV used (k >= ", mv_min_k,
        ", nClusters(id_1) >= 2, nClusters(id_2) >= 2, non-nested design)."
      )
      
      fitted_model <- tryCatch(
        metafor::rma.mv(
          yi = rg,
          V  = se^2,
          random = list(~1 | id_1, ~1 | id_2),
          data = meta_model_dt,
          method = "REML",
          test = "t"
        ),
        error = function(e) NULL
      )
      
      if (is.null(fitted_model)) {
        model_used <- "UNI"
        decision_reason <- "MV failed -> UNI fallback (REML + Knapp-Hartung)."
        fitted_model <- tryCatch(
          metafor::rma.uni(yi = meta_model_dt$rg, vi = meta_model_dt$se^2, method = "REML", test = "knha"),
          error = function(e) e
        )
      }
      
    } else {
      
      model_used <- "UNI"
      
      if (k_complete < mv_min_k) {
        decision_reason <- paste0("k < mv_min_k (", mv_min_k, ") -> UNI (REML + Knapp-Hartung).")
      } else if (nested_or_confounded) {
        decision_reason <- "Nested/confounded id_1-id_2 structure -> UNI (MV random effects not identifiable)."
      } else {
        decision_reason <- "Insufficient clusters for MV -> UNI (REML + Knapp-Hartung)."
      }
      
      fitted_model <- tryCatch(
        metafor::rma.uni(yi = meta_model_dt$rg, vi = meta_model_dt$se^2, method = "REML", test = "knha"),
        error = function(e) e
      )
    }
    
    if (inherits(fitted_model, "error") || is.null(fitted_model)) {
      out_fail <- data.frame(
        software = software_name,
        analysis_mode = analysis_mode_label,
        model_used = model_used,
        decision_reason = paste0(decision_reason, " (model fit error)"),
        robust_used_side = NA_character_,
        robust_decision_reason = NA_character_,
        
        disease_1 = d1, disease_2 = d2,
        k_raw = k_raw,
        k = k_complete,
        
        rg_res = NA_real_, se_res = NA_real_, zval_res = NA_real_, pval_res = NA_real_,
        ci_lb_res = NA_real_, ci_ub_res = NA_real_,
        het_res = NA_real_, pval_het_res = NA_real_,
        
        rg_rob1 = NA_real_, se_rob1 = NA_real_, t_rob1 = NA_real_, df_rob1 = NA_real_, p_rob1 = NA_real_,
        ci_lb_rob1 = NA_real_, ci_ub_rob1 = NA_real_,
        rg_rob2 = NA_real_, se_rob2 = NA_real_, t_rob2 = NA_real_, df_rob2 = NA_real_, p_rob2 = NA_real_,
        ci_lb_rob2 = NA_real_, ci_ub_rob2 = NA_real_,
        
        n_clusters_id1 = n_clusters_id1, n_clusters_id2 = n_clusters_id2,
        stringsAsFactors = FALSE
      )
      upsert_csv(results_csv_path, out_fail)
      return(out_fail)
    }
    
    model_for_plot <- fitted_model
    
    pooled_estimate <- as.numeric(fitted_model$b[1])
    pooled_se <- as.numeric(fitted_model$se[1])
    
    if (!is.null(fitted_model$tval)) {
      pooled_stat <- as.numeric(fitted_model$tval[1])
    } else if (!is.null(fitted_model$zval)) {
      pooled_stat <- as.numeric(fitted_model$zval[1])
    } else {
      pooled_stat <- if (!is.na(pooled_se) && pooled_se > 0) pooled_estimate / pooled_se else NA_real_
    }
    
    pooled_p <- as.numeric(fitted_model$pval[1])
    pooled_ci_lb <- as.numeric(fitted_model$ci.lb[1])
    pooled_ci_ub <- as.numeric(fitted_model$ci.ub[1])
    
    heterogeneity_QE  <- if (!is.null(fitted_model$QE))  as.numeric(fitted_model$QE)  else NA_real_
    heterogeneity_QEp <- if (!is.null(fitted_model$QEp)) as.numeric(fitted_model$QEp) else NA_real_
    
  }  # <-- closes the "else" for k_complete > 1
  
  k_used <- if (!is.null(model_for_plot) && !is.null(model_for_plot$k)) {
    as.integer(model_for_plot$k)
  } else {
    as.integer(k_complete)
  }
  # ---------------------------------------------------------------------------
  # 12) Robust SE via metafor::robust (clustered sandwich)
  # Why:
  # clubSandwich often fails with nested/confounded clustering. metafor::robust is
  # usually more stable; if it fails, we fall back to the model-based SE.
  # ---------------------------------------------------------------------------
  # Robust SE
  # - UNI: prefer clubSandwich CR2 (works well for rma.uni). If it fails, fallback to metafor::robust.
  # - MV : use metafor::robust (clubSandwich tends to fail with nested/random-effects structures).
  #
  # Thresholds:
  # - UNI: allow >= 2 clusters (user request)
  # - MV : keep more conservative >= 4 clusters by default (configurable)
  # ---------------------------------------------------------------------------
  
  extract_first_numeric <- function(obj, candidates) {
    for (nm in candidates) {
      if (!is.null(obj[[nm]])) return(as.numeric(obj[[nm]][1]))
    }
    NA_real_
  }
  
  safe_robust_uni <- function(model, cluster_vector) {
    if (is.null(model)) return(NULL)
    
    cluster_factor <- as.factor(clean_chr(cluster_vector))
    n_clust <- length(unique(cluster_factor[!is.na(cluster_factor)]))
    if (n_clust < 2) return(NULL)
    
    # Try clubSandwich first (best match to your old behavior)
    if (requireNamespace("clubSandwich", quietly = TRUE)) {
      rob_cs <- tryCatch(
        clubSandwich::coef_test(model, vcov = "CR2", cluster = cluster_factor),
        error = function(e) NULL
      )
      
      if (!is.null(rob_cs)) {
        # coef_test typically returns columns: beta, SE, tstat, df_Satt, p_Satt
        return(list(
          beta = as.numeric(rob_cs$beta[1]),
          SE   = as.numeric(rob_cs$SE[1]),
          stat = as.numeric(rob_cs$tstat[1]),
          df   = as.numeric(rob_cs$df_Satt[1]),
          p    = as.numeric(rob_cs$p_Satt[1]),
          n_clusters = n_clust,
          method = "clubSandwich_CR2"
        ))
      }
    }
    
    # Fallback to metafor::robust for UNI
    tryCatch({
      rob_mf <- metafor::robust(model, cluster = cluster_factor)
      
      stat_val <- extract_first_numeric(rob_mf, c("tval", "zval", "statistic"))
      df_val <- if (!is.null(rob_mf$ddf)) as.numeric(rob_mf$ddf[1]) else (n_clust - 1)
      
      list(
        beta = as.numeric(rob_mf$b[1]),
        SE   = as.numeric(rob_mf$se[1]),
        stat = stat_val,
        df   = df_val,
        p    = as.numeric(rob_mf$pval[1]),
        n_clusters = n_clust,
        method = "metafor_robust"
      )
    }, error = function(e) {
      
      # Last-resort fallback: model-based
      tryCatch({
        stat_val <- if (!is.null(model$tval)) as.numeric(model$tval[1]) else extract_first_numeric(model, c("zval"))
        list(
          beta = as.numeric(model$b[1]),
          SE   = as.numeric(model$se[1]),
          stat = stat_val,
          df   = (n_clust - 1),
          p    = as.numeric(model$pval[1]),
          n_clusters = n_clust,
          method = "model_based_fallback"
        )
      }, error = function(e2) NULL)
    })
  }
  
  safe_robust_mv <- function(model, cluster_vector) {
    if (is.null(model)) return(NULL)
    
    cluster_factor <- as.factor(clean_chr(cluster_vector))
    n_clust <- length(unique(cluster_factor[!is.na(cluster_factor)]))
    if (n_clust < 2) return(NULL)
    
    # For MV use metafor::robust (clubSandwich often fails with nested/confounded structures)
    tryCatch({
      rob <- metafor::robust(model, cluster = cluster_factor)
      
      stat_val <- extract_first_numeric(rob, c("tval", "zval", "statistic"))
      df_val <- if (!is.null(rob$ddf)) as.numeric(rob$ddf[1]) else (n_clust - 1)
      
      list(
        beta = as.numeric(rob$b[1]),
        SE   = as.numeric(rob$se[1]),
        stat = stat_val,
        df   = df_val,
        p    = as.numeric(rob$pval[1]),
        n_clusters = n_clust,
        method = "metafor_robust"
      )
    }, error = function(e) {
      
      # Last-resort fallback: model-based
      tryCatch({
        stat_val <- if (!is.null(model$tval)) as.numeric(model$tval[1]) else extract_first_numeric(model, c("zval"))
        list(
          beta = as.numeric(model$b[1]),
          SE   = as.numeric(model$se[1]),
          stat = stat_val,
          df   = (n_clust - 1),
          p    = as.numeric(model$pval[1]),
          n_clusters = n_clust,
          method = "model_based_fallback"
        )
      }, error = function(e2) NULL)
    })
  }
  
  min_clusters_for_robust <- if (model_used == "MV") robust_min_clusters_mv else robust_min_clusters_uni
  
  # Compute robust on each side if cluster count meets threshold
  robust_id1 <- NULL
  robust_id2 <- NULL
  
  if (n_clusters_id1 >= min_clusters_for_robust) {
    robust_id1 <- if (model_used == "MV") {
      safe_robust_mv(model_for_plot, meta_model_dt$id_1)
    } else {
      safe_robust_uni(model_for_plot, meta_model_dt$id_1)
    }
  }
  
  if (n_clusters_id2 >= min_clusters_for_robust) {
    robust_id2 <- if (model_used == "MV") {
      safe_robust_mv(model_for_plot, meta_model_dt$id_2)
    } else {
      safe_robust_uni(model_for_plot, meta_model_dt$id_2)
    }
  }
  
  compute_robust_ci <- function(rob_obj) {
    if (is.null(rob_obj)) return(c(NA_real_, NA_real_))
    beta <- as.numeric(rob_obj$beta)
    se   <- as.numeric(rob_obj$SE)
    df   <- as.numeric(rob_obj$df)
    if (is.na(df) || df <= 0 || is.na(se)) return(c(NA_real_, NA_real_))
    c(beta - stats::qt(0.975, df = df) * se, beta + stats::qt(0.975, df = df) * se)
  }
  
  ci_id1 <- compute_robust_ci(robust_id1)
  ci_id2 <- compute_robust_ci(robust_id2)
  
  # ---------------------------------------------------------------------------
  # 13) Decide which robust result to highlight
  # Conservative rule:
  # If both are available, pick the one with the larger robust SE (more conservative).
  # Tie-break: smaller df (also more conservative).
  # ---------------------------------------------------------------------------
  robust_used_side <- NA_character_
  robust_decision_reason <- "No robust estimation available."
  
  has_id1 <- !is.null(robust_id1)
  has_id2 <- !is.null(robust_id2)
  
  if (has_id1 || has_id2) {
    if (has_id1 && has_id2) {
      
      se1 <- robust_id1$SE; se2 <- robust_id2$SE
      df1 <- robust_id1$df; df2 <- robust_id2$df
      
      if (is.na(se1) && !is.na(se2)) {
        robust_used_side <- "id_2"
      } else if (!is.na(se1) && is.na(se2)) {
        robust_used_side <- "id_1"
      } else if (!is.na(se1) && !is.na(se2) && se1 > se2) {
        robust_used_side <- "id_1"
      } else if (!is.na(se1) && !is.na(se2) && se2 > se1) {
        robust_used_side <- "id_2"
      } else {
        if (!is.na(df1) && !is.na(df2) && df1 <= df2) robust_used_side <- "id_1" else robust_used_side <- "id_2"
      }
      
      robust_decision_reason <- paste0(
        "Robust SE computed for UNI/MV (both sides available). Selected conservative side. ",
        "UNI method: clubSandwich CR2 with metafor fallback; MV method: metafor::robust."
      )
      
    } else if (has_id1) {
      robust_used_side <- "id_1"
      robust_decision_reason <- "Robust SE computed for id_1 only (other side below threshold or failed)."
    } else {
      robust_used_side <- "id_2"
      robust_decision_reason <- "Robust SE computed for id_2 only (other side below threshold or failed)."
    }
  } else {
    if (n_clusters_id1 < min_clusters_for_robust && n_clusters_id2 < min_clusters_for_robust) {
      robust_decision_reason <- paste0(
        "Insufficient clusters for robust SE. ",
        "nClusters(id_1)=", n_clusters_id1, ", nClusters(id_2)=", n_clusters_id2,
        ", threshold=", min_clusters_for_robust, "."
      )
    } else {
      robust_decision_reason <- "Robust SE computation failed."
    }
  }
  
  # ---------------------------------------------------------------------------
  # 14) Build the output row (kept compatible with your existing CSV schema)
  # ---------------------------------------------------------------------------
  get_beta <- function(x) if (is.null(x)) NA_real_ else as.numeric(x$beta)
  get_se   <- function(x) if (is.null(x)) NA_real_ else as.numeric(x$SE)
  get_stat <- function(x) if (is.null(x)) NA_real_ else as.numeric(x$stat)
  get_df   <- function(x) if (is.null(x)) NA_real_ else as.numeric(x$df)
  get_p    <- function(x) if (is.null(x)) NA_real_ else as.numeric(x$p)
  
  out_row <- data.frame(
    software = software_name,
    analysis_mode = analysis_mode_label,
    model_used = model_used,
    decision_reason = decision_reason,
    robust_used_side = robust_used_side,
    robust_decision_reason = robust_decision_reason,
    
    disease_1 = d1,
    disease_2 = d2,
    k_raw = k_raw,
    k = k_used,
    
    rg_res = pooled_estimate,
    se_res = pooled_se,
    zval_res = pooled_stat,
    pval_res = pooled_p,
    ci_lb_res = pooled_ci_lb,
    ci_ub_res = pooled_ci_ub,
    het_res = heterogeneity_QE,
    pval_het_res = heterogeneity_QEp,
    
    rg_rob1 = get_beta(robust_id1),
    se_rob1 = get_se(robust_id1),
    t_rob1  = get_stat(robust_id1),
    df_rob1 = get_df(robust_id1),
    p_rob1  = get_p(robust_id1),
    ci_lb_rob1 = ci_id1[1],
    ci_ub_rob1 = ci_id1[2],
    
    rg_rob2 = get_beta(robust_id2),
    se_rob2 = get_se(robust_id2),
    t_rob2  = get_stat(robust_id2),
    df_rob2 = get_df(robust_id2),
    p_rob2  = get_p(robust_id2),
    ci_lb_rob2 = ci_id2[1],
    ci_ub_rob2 = ci_id2[2],
    
    n_clusters_id1 = n_clusters_id1,
    n_clusters_id2 = n_clusters_id2,
    stringsAsFactors = FALSE
  )
  
  upsert_csv(results_csv_path, out_row)
  
  # ---------------------------------------------------------------------------
  # 15) Forest plot output
  # Note:
  # - We plot the model object (UNI or MV). For k=1 we plot a FE placeholder.
  # - We annotate with Study IDs, selections, and per-row p-values.
  # - We add a line with model p-value and robust p-value when available.
  # ---------------------------------------------------------------------------
  plot_dir <- file.path(output_folder, software_name)
  if (!dir.exists(plot_dir)) dir.create(plot_dir, recursive = TRUE)
  
  plot_title <- paste0(d1, " vs ", d2, " - ", software_name, " (", model_used, ")")
  selection_label <- paste0(meta_model_dt$selection_1, " - ", meta_model_dt$selection_2)
  
  output_path <- file.path(
    plot_dir,
    paste0(d1, " & ", d2,
           if (just_main_minor) " forest plot" else " forest plot Subtypes",
           if (software_name == "LDSC") " LDSC.pdf" else " HDL.pdf")
  )
  
  id1_label <- ifelse(is.na(meta_model_dt$disease_subtype_1) | meta_model_dt$disease_subtype_1 == "",
                      meta_model_dt$id_1,
                      paste0(meta_model_dt$id_1, " (", meta_model_dt$disease_subtype_1, ")"))
  
  id2_label <- ifelse(is.na(meta_model_dt$disease_subtype_2) | meta_model_dt$disease_subtype_2 == "",
                      meta_model_dt$id_2,
                      paste0(meta_model_dt$id_2, " (", meta_model_dt$disease_subtype_2, ")"))
  
  p_display <- ifelse(is.na(meta_model_dt$p), "NA",
                      paste0(formatC(meta_model_dt$p, digits = 2, format = "f"), meta_model_dt$sig_star))
  
  ilab_mat <- cbind(id1_label, id2_label, selection_label, p_display)
  
  xpos <- c(-4, -3, -1.5, 1.5)
  xlims <- c(-4.5, 2.5)
  alims <- c(-1.0, 1.0)
  
  k_plot <- nrow(meta_model_dt)
  row_spacing <- 1.5
  plot_rows <- (k_plot:1) * row_spacing
  pdf_height <- max(7, 0.18 * k_plot * row_spacing + 3)
  
  grDevices::pdf(file = output_path, width = 16, height = pdf_height)
  
  if (!is.null(model_for_plot)) {
    metafor::forest(
      model_for_plot,
      slab = rep("", k_plot),
      ilab = ilab_mat,
      ilab.xpos = xpos,
      xlim = xlims,
      alim = alims,
      xlab = "Genetic correlation (rg)",
      cex = 0.8,
      rows = plot_rows,
      ylim = c(-4, max(plot_rows) + 3.5),
      main = plot_title,
      header = ""
    )
  } else {
    plot.new()
    title(main = plot_title)
    text(0.5, 0.5, "Plot not available.")
  }
  
  header_y <- max(plot_rows) + 2.1
  text(x = mean(xpos[1:2]), y = max(plot_rows) + 3, labels = "Study ID", cex = 0.8, font = 2)
  text(x = xpos, y = header_y, labels = c(d1, d2, "Selection", "Pval (FDR*)"), cex = 0.8, font = 2)
  
  model_p_text <- if (!is.na(out_row$pval_res)) {
    paste0(formatC(out_row$pval_res, digits = 2, format = "f"), if (out_row$pval_res < 0.05) "*" else "")
  } else {
    "NA"
  }
  text(x = xpos[4] - 0.1, y = -1, pos = 4, cex = 0.8, labels = model_p_text)
  
  # Robust annotation (only if we selected a robust side and p is available)
  if (!is.na(out_row$robust_used_side)) {
    
    rob_p   <- if (out_row$robust_used_side == "id_1") out_row$p_rob1  else out_row$p_rob2
    rob_val <- if (out_row$robust_used_side == "id_1") out_row$rg_rob1 else out_row$rg_rob2
    rob_ci  <- if (out_row$robust_used_side == "id_1") c(out_row$ci_lb_rob1, out_row$ci_ub_rob1) else c(out_row$ci_lb_rob2, out_row$ci_ub_rob2)
    
    if (!is.na(rob_p)) {
      rob_col <- "darkblue"
      y_p <- -2.0
      dy <- 0.9
      y_lab <- y_p - dy
      
      robust_p_text <- paste0(formatC(rob_p, digits = 2, format = "f"), if (rob_p <= 0.05) "*" else "")
      
      text(x = xpos[4] - 0.1, y = y_p, pos = 4, cex = 0.8, col = rob_col, labels = robust_p_text)
      
      ci_line <- paste0(
        formatC(rob_val, digits = 2, format = "f"),
        " [", formatC(rob_ci[1], digits = 2, format = "f"),
        ",  ", formatC(rob_ci[2], digits = 2, format = "f"), "]"
      )
      text(x = xlims[2], y = y_p, pos = 2, cex = 0.8, col = rob_col, labels = ci_line)
      
      text(
        x = xlims[2], y = y_lab, pos = 2, cex = 0.8, font = 2, col = rob_col,
        labels = paste0("Robust corrected values (", out_row$robust_used_side, ")")
      )
    }
  }
  
  abline(v = 0, lty = 2, col = "gray60")
  grDevices::dev.off()
  
  return(out_row)
}

# metafor_process <- function(software_df, software_name, d1, d2, just_main_minor = TRUE, output_folder) {
#   # Checkpoint para evitar problemas de selección
#   stopifnot(is.logical(just_main_minor))
#   
#   analysis_label <- if (just_main_minor) "Main_Minor" else "All"
#   
#   # First manage df
#   ## Select d1 and d2 only
#   df <- software_df[(software_df$disease_1 == d1 & software_df$disease_2 == d2) | 
#                       (software_df$disease_1 == d2 & software_df$disease_2 == d1),]
#   message("Rows after disease filter: ", nrow(df))
#   
#   ## Filter by selection if necessary
#   if (just_main_minor) {
#     print("Selected just main and minor datasets")
#     df <- subset(df, selection_1 %in% c("main","minor") & selection_2 %in% c("main","minor"))
#   } else {
#     print("Selected all datasets (including subtypes)")
#   }
#   message("Rows after selection filter: ", nrow(df))
#   
#   results_csv <- file.path(output_folder, paste0("0_", software_name, "_meta_results.csv"))
#   if (!dir.exists(output_folder)) dir.create(output_folder, recursive = TRUE)
#   
#   # If empty dataframe
#   if (nrow(df) == 0) {
#     out_empty <- data.frame(
#       software = software_name,
#       analysis_mode = analysis_label, 
#       disease_1 = d1, 
#       disease_2 = d2,
#       k = 0,
#       rg_res = NA_real_, se_res = NA_real_, zval_res = NA_real_, pval_res = NA_real_,
#       ci_lb_res = NA_real_, ci_ub_res = NA_real_,
#       het_res = NA_real_, pval_het_res = NA_real_,
#       rg_rob1 = NA_real_, se_rob1 = NA_real_, t_rob1 = NA_real_, df_rob1 = NA_real_, p_rob1 = NA_real_,
#       rg_rob2 = NA_real_, se_rob2 = NA_real_, t_rob2 = NA_real_, df_rob2 = NA_real_, p_rob2 = NA_real_,
#       n_clusters_id1 = NA_integer_, n_clusters_id2 = NA_integer_,
#       stringsAsFactors = FALSE
#     )
#     
#     if (file.exists(results_csv)) {
#       old_data <- read.csv(results_csv, stringsAsFactors = FALSE)
#       if (!"analysis_mode" %in% colnames(old_data)) old_data$analysis_mode <- "Unknown"
#       old_data <- old_data[!(old_data$software == software_name & 
#                                old_data$disease_1 == d1 & 
#                                old_data$disease_2 == d2 &
#                                old_data$analysis_mode == analysis_label), ]
#       out_to_write <- rbind(old_data, out_empty)
#       write.csv(out_to_write, results_csv, row.names = FALSE)
#     } else {
#       write.csv(out_empty, results_csv, row.names = FALSE)
#     }
#     return(out_empty)
#   }
#   
#   # Select columns 
#   cols_used <- c("disease_1", "disease_subtype_1", "disease_2", "disease_subtype_2", 
#                  "selection_1", "id_1", "selection_2" ,"id_2", "label_1", "label_2", 
#                  "Nca_val_1", "N_num_1", "Nca_val_2", "N_num_2",
#                  "rg", "se", "p", "p_corrected_FDR", "p_FDR_rejected")
#   
#   dat <- df[, ..cols_used]
#   
#   ## Re order dat for by pairing
#   dat$order_plot <- with(dat,
#                          ifelse(selection_1 == "main" & selection_2 == "main", 1,
#                                 ifelse(selection_1 == "main" & selection_2 == "minor", 2,
#                                        ifelse(selection_1 == "minor" & selection_2 == "main", 3,
#                                               ifelse(selection_1 == "minor" & selection_2 == "minor", 4,
#                                                      ifelse(selection_1 == "main" & selection_2 == "subtype", 5,
#                                                             ifelse(selection_1 == "minor" & selection_2 == "subtype", 6,
#                                                                    ifelse(selection_1 == "main" & selection_2 == "subtype-family", 7,
#                                                                           ifelse(selection_1 == "minor" & selection_2 == "subtype-family", 8,
#                                                                                  ifelse(selection_1 == "subtype" & selection_2 == "main", 9,
#                                                                                         ifelse(selection_1 == "subtype" & selection_2 == "minor", 10,
#                                                                                                ifelse(selection_1 == "subtype-family" & selection_2 == "main", 11,
#                                                                                                       ifelse(selection_1 == "subtype-family" & selection_2 == "minor", 12, 13)))))))))))))
#   dat <- dat[order(dat$order_plot), ]
#   dat$sig_star <- ifelse(!is.na(dat$p_FDR_rejected) & dat$p_FDR_rejected, "*", "")
#   
#   # Metaanalysis random-effects (REML)
#   res <- tryCatch(
#     rma.uni(yi = dat$rg, vi = dat$se^2, method = "REML", test="knha"),
#     error = function(e) e
#   )
#   
#   # Raise error
#   if (inherits(res, "error")) {
#     out_fail <- data.frame(
#       software = software_name,
#       analysis_mode = analysis_label,
#       disease_1 = d1, disease_2 = d2,
#       k = nrow(dat),
#       rg_res = NA_real_, se_res = NA_real_, zval_res = NA_real_, pval_res = NA_real_,
#       ci_lb_res = NA_real_, ci_ub_res = NA_real_,
#       het_res = NA_real_, pval_het_res = NA_real_,
#       rg_rob1 = NA_real_, se_rob1 = NA_real_, t_rob1 = NA_real_, df_rob1 = NA_real_, p_rob1 = NA_real_,
#       rg_rob2 = NA_real_, se_rob2 = NA_real_, t_rob2 = NA_real_, df_rob2 = NA_real_, p_rob2 = NA_real_,
#       stringsAsFactors = FALSE
#     )
#     
#     if (file.exists(results_csv)) {
#       old_data <- read.csv(results_csv, stringsAsFactors = FALSE)
#       if (!"analysis_mode" %in% colnames(old_data)) old_data$analysis_mode <- "Unknown"
#       old_data <- old_data[!(old_data$software == software_name & 
#                                old_data$disease_1 == d1 & 
#                                old_data$disease_2 == d2 &
#                                old_data$analysis_mode == analysis_label), ]
#       out_to_write <- rbind(old_data, out_fail)
#       write.csv(out_to_write, results_csv, row.names = FALSE)
#     } else {
#       write.csv(out_fail, results_csv, row.names = FALSE)
#     }
#     return(out_fail)
#   }
#   
#   ## Robust SE
#   ncl_id1 <- length(unique(dat$id_1))
#   ncl_id2 <- length(unique(dat$id_2))
#   rob_id1 <- tryCatch(clubSandwich::coef_test(res, vcov = "CR2", cluster = dat$id_1), error = function(e) NULL)
#   rob_id2 <- tryCatch(clubSandwich::coef_test(res, vcov = "CR2", cluster = dat$id_2), error = function(e) NULL)
#   
#   # CI para robustez
#   est <- as.numeric(res$b[1])
#   calc_ci_rob <- function(rob_obj) {
#     if (is.null(rob_obj)) return(c(NA_real_, NA_real_))
#     se <- as.numeric(rob_obj$SE[1])
#     df_satt <- as.numeric(rob_obj$df_Satt[1])
#     c(est - qt(0.975, df = df_satt) * se, est + qt(0.975, df = df_satt) * se)
#   }
#   ci_1 <- calc_ci_rob(rob_id1); ci_2 <- calc_ci_rob(rob_id2)
#   
#   # Save results from metaanalysis
#   out_row <- data.frame(
#     software = software_name,
#     analysis_mode = analysis_label,
#     disease_1 = d1, disease_2 = d2,
#     k = res$k,
#     rg_res = as.numeric(res$b[1]),
#     se_res = as.numeric(res$se[1]),
#     zval_res = as.numeric(res$zval[1]),
#     pval_res = as.numeric(res$pval[1]),
#     ci_lb_res = as.numeric(res$ci.lb[1]),
#     ci_ub_res = as.numeric(res$ci.ub[1]),
#     het_res = as.numeric(res$QE),
#     pval_het_res = as.numeric(res$QEp),
#     rg_rob1 = if (!is.null(rob_id1)) as.numeric(rob_id1$beta[1]) else NA_real_,
#     se_rob1 = if (!is.null(rob_id1)) as.numeric(rob_id1$SE[1]) else NA_real_,
#     t_rob1  = if (!is.null(rob_id1)) as.numeric(rob_id1$tstat[1]) else NA_real_,
#     df_rob1 = if (!is.null(rob_id1)) as.numeric(rob_id1$df_Satt[1]) else NA_real_,
#     p_rob1  = if (!is.null(rob_id1)) as.numeric(rob_id1$p_Satt[1]) else NA_real_,
#     ci_lb_rob1 = ci_1[1], ci_ub_rob1 = ci_1[2],
#     rg_rob2 = if (!is.null(rob_id2)) as.numeric(rob_id2$beta[1]) else NA_real_,
#     se_rob2 = if (!is.null(rob_id2)) as.numeric(rob_id2$SE[1]) else NA_real_,
#     t_rob2  = if (!is.null(rob_id2)) as.numeric(rob_id2$tstat[1]) else NA_real_,
#     df_rob2 = if (!is.null(rob_id2)) as.numeric(rob_id2$df_Satt[1]) else NA_real_,
#     p_rob2  = if (!is.null(rob_id2)) as.numeric(rob_id2$p_Satt[1]) else NA_real_,
#     ci_lb_rob2 = ci_2[1], ci_ub_rob2 = ci_2[2],
#     n_clusters_id1 = ncl_id1,
#     n_clusters_id2 = ncl_id2,
#     stringsAsFactors = FALSE
#   )
#   
#   # Save csv
#   if (file.exists(results_csv)) {
#     old_data <- read.csv(results_csv, stringsAsFactors = FALSE)
#     if (!"analysis_mode" %in% colnames(old_data)) old_data$analysis_mode <- "Unknown"
#     old_data <- old_data[!(old_data$software == software_name & 
#                              old_data$disease_1 == d1 & 
#                              old_data$disease_2 == d2 &
#                              old_data$analysis_mode == analysis_label), ]
#     out_to_write <- rbind(old_data, out_row)
#     write.csv(out_to_write, results_csv, row.names = FALSE)
#   } else {
#     write.csv(out_row, results_csv, row.names = FALSE)
#   }
#   
#   # PLOT
#   plot_title <- paste0(d1, " vs ", d2, " - ", software_name)
#   sel_cat <- paste0(dat$selection_1, " - ", dat$selection_2)
#   
#   output_path <- file.path(paste0(output_folder, "/", software_name), paste0(d1, " & ", d2,
#                                                  if(just_main_minor) " forest plot" else " forest plot Subtypes",
#                                                  if (software_name == "LDSC") " LDSC.pdf" else " HDL.pdf"))
#   
#   id1_label_wsubtype <- ifelse(is.na(dat$disease_subtype_1) | dat$disease_subtype_1 == "", dat$id_1, paste0(dat$id_1, " (", dat$disease_subtype_1, ")"))
#   id2_label_wsubtype <- ifelse(is.na(dat$disease_subtype_2) | dat$disease_subtype_2 == "", dat$id_2, paste0(dat$id_2, " (", dat$disease_subtype_2, ")"))
#   
#   ilab_mat <- cbind(id1_label_wsubtype, id2_label_wsubtype, sel_cat, paste0(formatC(dat$p, digits=2, format="f"), dat$sig_star))
#   
#   xpos <- c(-4, -3, -1.5, 1.5); xlims <- c(-4.5, 2.5); alims <- c(-1.0, 1.0)
#   k_plot <- nrow(dat); rows_spacing <- 1.5; rows_plot <- (k_plot:1) * rows_spacing
#   pdf_height <- max(7, 0.18 * k_plot * rows_spacing + 3)
#   
#   pdf(file = output_path, width = 16, height = pdf_height)
#   forest(res, slab = rep("", res$k), ilab = ilab_mat, ilab.xpos = xpos, xlim = xlims, alim = alims,
#          xlab = "Genetic correlation (rg)", cex = 0.8, rows = rows_plot, ylim = c(-4, max(rows_plot) + 3.5))
#   
#   # Header
#   header_y <- max(rows_plot) + 2.1
#   text(x = mean(xpos[1:2]), y = max(rows_plot) + 3, labels = "Study ID", cex = 0.8, font = 2)
#   text(x = xpos, y = header_y, labels = c(d1, d2, "Selection", "Pval(FDR*)"), cex = 0.8, font = 2)
#   
#   # P-value res
#   p_text <- paste0(formatC(out_row$pval_res, digits=2, format="f"), if(out_row$pval_res < 0.05) "*" else "")
#   text(x = xpos[4]-0.1, y = -1, pos = 4, cex = 0.8, p_text)
#   
#   # P-value rob
#   if (!(ncl_id1 == out_row$k && ncl_id2 == out_row$k)) {
#     use_rob1 <- ncl_id1 <= ncl_id2
#     rob_p <- if(use_rob1) out_row$p_rob1 else out_row$p_rob2
#     text_prob <- paste0(formatC(rob_p, digits=2, format="f"), if(rob_p <= 0.05) "*" else "")
#     text(x = xpos[4]-0.1, y = -2.3, pos = 4, cex = 0.8, text_prob)
#   }
# 
#   
#   # Robustness label
#   if (!(ncl_id1 == out_row$k && ncl_id2 == out_row$k)) {
#     use_rob1 <- ncl_id1 <= ncl_id2
#     rob_val <- if(use_rob1) out_row$rg_rob1 else out_row$rg_rob2
#     rob_p <- if(use_rob1) out_row$p_rob1 else out_row$p_rob2
#     rob_ci <- if(use_rob1) c(out_row$ci_lb_rob1, out_row$ci_ub_rob1) else c(out_row$ci_lb_rob2, out_row$ci_ub_rob2)
#     
#     text_rob <- paste0("ROB = ", formatC(rob_val, digits=2, format="f"),
#                        " [ ", formatC(rob_ci[1], digits=2, format="f"), ",  ", formatC(rob_ci[2], digits=2, format="f"), "]")
#     text(x = xlims[2], y = -2.3, pos = 2, cex = 0.8, text_rob)
#   }
#   
#   abline(v = 0, lty = 2, col = "gray60")
#   dev.off()
#   
#   return(out_row)
# }

# metafor_process(ldsc_no_self_pairs, "LDSC", "major depression disorder", "skin cancer", just_main_minor = T, metaanalisis_save)
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "major depression disorder", "skin cancer", just_main_minor = F, metaanalisis_save)

# metafor_process(hdl_no_self_pairs, "HDL", "autism", "schizophrenia", just_main_minor = T, metaanalisis_save)
# 
# metafor_process(hdl_no_self_pairs, "HDL", "major depression disorder", "skin cancer", just_main_minor = F, metaanalisis_save)
# 
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "autism", "amyotrophic lateral sclerosis", just_main_minor = T, metaanalisis_save)
# 
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "attention deficit disorder", "cervical cancer", just_main_minor = T, metaanalisis_save)
# metafor_process(ldsc_no_self_pairs, "LDSC", "attention deficit disorder", "cervical cancer", just_main_minor = F, metaanalisis_save)
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "lung cancer", just_main_minor = T, metaanalisis_save)
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "lung cancer", just_main_minor = F, metaanalisis_save)
# 
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "alzheimer's disease", just_main_minor = T, metaanalisis_save)
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "alzheimer's disease", just_main_minor = F, metaanalisis_save)
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "parkison's disease", just_main_minor = T, metaanalisis_save)
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "parkison's disease", just_main_minor = F, metaanalisis_save)
# 
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "alzheimer's disease", "schizophrenia", just_main_minor = T, metaanalisis_save)
# metafor_process(ldsc_no_self_pairs, "LDSC", "alzheimer's disease", "schizophrenia", just_main_minor = F, metaanalisis_save)
# 
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "alzheimer's disease", "skin cancer", just_main_minor = T, metaanalisis_save)
# metafor_process(ldsc_no_self_pairs, "LDSC", "alzheimer's disease", "skin cancer", just_main_minor = F, metaanalisis_save)
# 
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "melanoma", just_main_minor = T, metaanalisis_save)
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "melanoma", just_main_minor = F, metaanalisis_save)
# 
# metafor_process(ldsc_no_self_pairs, "LDSC", "breast cancer", "lymph node cancer", just_main_minor = T, metaanalisis_save)

# metafor_process(ldsc_no_self_pairs, "LDSC", "uterus cancer", "uterus polyps", just_main_minor = T, metaanalisis_save)
# 
# 

ldsc_unique_pairs_t <- ldsc_unique_pairs[1:5,]
for (i in 1:nrow(ldsc_unique_pairs)) {
  
  # Extraemos los nombres de las enfermedades de la fila actual
  current_d1 <- ldsc_unique_pairs$d1[i]
  current_d2 <- ldsc_unique_pairs$d2[i]
  
  message(paste0(">>> Procesando par ", i, " de ", nrow(ldsc_unique_pairs), ": ", current_d1, " - ", current_d2))
  
  # Llamamos a tu función corregida
  # Nota: usamos ldsc (el original) para que la función tenga todos los datos para filtrar
  tryCatch({
    metafor_process(
      software_df = ldsc, 
      software_name = "LDSC", 
      d1 = current_d1, 
      d2 = current_d2, 
      just_main_minor = TRUE, 
      output_folder = metaanalisis_save
    )
  }, error = function(e) {
    message(paste0("Error main_minor: ", current_d1, " - ", current_d2, " : ", e$message))
  })
  
  tryCatch({
    metafor_process(
      software_df = ldsc, 
      software_name = "LDSC", 
      d1 = current_d1, 
      d2 = current_d2, 
      just_main_minor = FALSE, 
      output_folder = metaanalisis_save
    )
  }, error = function(e) {
    message(paste0("Error all: ", current_d1, " - ", current_d2, " : ", e$message))
  })
}







for (i in 1:nrow(hdl_unique_pairs)) {
  
  # Extraemos los nombres de las enfermedades de la fila actual
  current_d1 <- hdl_unique_pairs$d1[i]
  current_d2 <- hdl_unique_pairs$d2[i]
  
  message(paste0(">>> Procesando par ", i, " de ", nrow(hdl_unique_pairs), ": ", current_d1, " - ", current_d2))
  
  # Llamamos a tu función corregida
  # Nota: usamos hdl (el original) para que la función tenga todos los datos para filtrar
  tryCatch({
    metafor_process(
      software_df = hdl, 
      software_name = "HDL", 
      d1 = current_d1, 
      d2 = current_d2, 
      just_main_minor = TRUE, 
      output_folder = metaanalisis_save
    )
  }, error = function(e) {
    message(paste0("Error main_minor: ", current_d1, " - ", current_d2, " : ", e$message))
  })
  
  tryCatch({
    metafor_process(
      software_df = hdl, 
      software_name = "HDL", 
      d1 = current_d1, 
      d2 = current_d2, 
      just_main_minor = FALSE, 
      output_folder = metaanalisis_save
    )
  }, error = function(e) {
    message(paste0("Error all: ", current_d1, " - ", current_d2, " : ", e$message))
  })
}





#############################
# Simplified table for later 

extract_clean_results <- function(meta_df) {
  meta_df %>%
    mutate(
      rg_final = case_when(
        robust_used_side == "id_1" ~ rg_rob1,
        robust_used_side == "id_2" ~ rg_rob2,
        TRUE ~ rg_res
      ),
      p_final = case_when(
        robust_used_side == "id_1" ~ p_rob1,
        robust_used_side == "id_2" ~ p_rob2,
        TRUE ~ pval_res
      )
    ) %>%
    select(disease_1, disease_2, rg = rg_final, p = p_final, analysis_mode)
}


#############################
select_results_for_comparison <- function(df_software, alpha = 0.05) {
  # -------------------------------------------------------------------------
  # Build:
  # 1) all_results: one row per disease pair with model + robust information
  # 2) sig_model_uncorrected: significant by model p-value (pval_res), no correction
  # 3) sig_robust_only: significant by the *selected* robust p-value
  #
  # Key design choice:
  # - We DO NOT re-decide the robust side here.
  #   We use robust_used_side produced by the meta-analysis function,
  #   so plots/CSV/filters stay consistent.
  # -------------------------------------------------------------------------
  
  suppressPackageStartupMessages(library(dplyr))
  
  all_results <- df_software %>%
    mutate(
      # -------------------------
      # Model-based results
      # -------------------------
      model_rg = rg_res,
      model_p  = pval_res,
      model_sig = !is.na(model_p) & model_p <= alpha,
      
      # -------------------------
      # Robust results by each side (if available)
      # -------------------------
      rob1_sig = !is.na(p_rob1) & p_rob1 <= alpha,
      rob2_sig = !is.na(p_rob2) & p_rob2 <= alpha,
      
      # -------------------------
      # Robust results following the chosen side in your pipeline
      # -------------------------
      robust_selected_side = robust_used_side,
      robust_rg = case_when(
        robust_used_side == "id_1" ~ rg_rob1,
        robust_used_side == "id_2" ~ rg_rob2,
        TRUE ~ NA_real_
      ),
      robust_p = case_when(
        robust_used_side == "id_1" ~ p_rob1,
        robust_used_side == "id_2" ~ p_rob2,
        TRUE ~ NA_real_
      ),
      robust_se = case_when(
        robust_used_side == "id_1" ~ se_rob1,
        robust_used_side == "id_2" ~ se_rob2,
        TRUE ~ NA_real_
      ),
      robust_df = case_when(
        robust_used_side == "id_1" ~ df_rob1,
        robust_used_side == "id_2" ~ df_rob2,
        TRUE ~ NA_real_
      ),
      robust_sig = !is.na(robust_p) & robust_p <= alpha
    ) %>%
    select(
      software, analysis_mode,
      disease_1, disease_2,
      model_used, decision_reason, robust_decision_reason,
      k_raw, k,
      het_res, pval_het_res,
      
      # Model
      model_rg, model_p, model_sig,
      
      # Robust (both sides)
      rg_rob1, se_rob1, df_rob1, p_rob1, rob1_sig, n_clusters_id1,
      rg_rob2, se_rob2, df_rob2, p_rob2, rob2_sig, n_clusters_id2,
      
      # Robust (selected)
      robust_selected_side, robust_rg, robust_se, robust_df, robust_p, robust_sig
    ) %>%
    as.data.frame()
  
  sig_model_uncorrected <- all_results %>%
    filter(model_sig) %>%
    as.data.frame()
  
  sig_robust_only <- all_results %>%
    filter(robust_sig) %>%
    as.data.frame()
  
  return(list(
    all_results = all_results,
    sig_model_uncorrected = sig_model_uncorrected,
    sig_robust_only = sig_robust_only
  ))
}


# -------------------------------------------------------------------------
#   1) ALL results (for comparison): model + robust (both sides + selected side)
#   2) Significant by MODEL p-value (uncorrected): sig_model_uncorrected
#   3) Significant by ROBUST p-value (selected side): sig_robust_only
# -------------------------------------------------------------------------

###### Select from LDSC
meta_ldsc <- fread(paste0(metaanalisis_save, "0_LDSC_meta_results.csv"), sep = ",")

#First simplified versions for later use
simplified_meta_ldsc <- extract_clean_results(meta_ldsc)
save_path_simplified_meta_ldsc <- paste0(metaanalisis_save, "ldsc_meta_simplified.csv")
write.csv(simplified_meta_ldsc, save_path_simplified_meta_ldsc, row.names = FALSE)


#Save the other tables
meta_ldsc_main_minor <- dplyr::filter(meta_ldsc, analysis_mode == "Main_Minor")
ldsc_out <- select_results_for_comparison(meta_ldsc_main_minor, alpha = 0.05)

ldsc_all_results   <- ldsc_out$all_results
ldsc_sig_model     <- ldsc_out$sig_model_uncorrected
ldsc_sig_robust    <- ldsc_out$sig_robust_only

ldsc_all_results$Software <- "LDSC"
ldsc_sig_model$Software   <- "LDSC"
ldsc_sig_robust$Software  <- "LDSC"


###### Select from HDL
meta_hdl <- fread(paste0(metaanalisis_save, "0_HDL_meta_results.csv"), sep = ",")

#First simplified versions for later use
simplified_meta_hdl <- extract_clean_results(meta_hdl)
save_path_simplified_meta_hdl <- paste0(metaanalisis_save, "hdl_meta_simplified.csv")
write.csv(simplified_meta_hdl, save_path_simplified_meta_hdl, row.names = FALSE)


#Save the other tables
meta_hdl_main_minor <- dplyr::filter(meta_hdl, analysis_mode == "Main_Minor")
hdl_out <- select_results_for_comparison(meta_hdl_main_minor, alpha = 0.05)

hdl_all_results   <- hdl_out$all_results
hdl_sig_model     <- hdl_out$sig_model_uncorrected
hdl_sig_robust    <- hdl_out$sig_robust_only

hdl_all_results$Software <- "HDL"
hdl_sig_model$Software   <- "HDL"
hdl_sig_robust$Software  <- "HDL"


# -------------------------------------------------------------------------
# Combine and save
# - "ALL" table is useful to compare model vs robust side-by-side
# - "MODEL" and "ROBUST" are the filtered significant sets
# -------------------------------------------------------------------------

all_results_all <- dplyr::bind_rows(ldsc_all_results, hdl_all_results)
sig_model_all   <- dplyr::bind_rows(ldsc_sig_model,   hdl_sig_model)
sig_robust_all  <- dplyr::bind_rows(ldsc_sig_robust,  hdl_sig_robust)

# Minimal columns for your previous outputs (kept compatible)
cols_minimal <- c("disease_1", "disease_2", "Software")

# For MODEL-significant, use model_rg
sig_model_min <- sig_model_all %>%
  dplyr::select(all_of(cols_minimal), rg = model_rg) %>%
  as.data.frame()

# For ROBUST-significant, use robust_rg (selected robust side)
sig_robust_min <- sig_robust_all %>%
  dplyr::select(all_of(cols_minimal), rg = robust_rg) %>%
  as.data.frame()

# (Optional) Save the full comparison table (recommended)
save_path_all_results <- paste0(wd, "/Results/ldsc_hdl_meta_ALL_for_comparison.csv")

# Save paths (same naming as before, but MODEL instead of TEST)
save_path_meta_model  <- paste0(wd, "/Results/ldsc_hdl_meta_significant_MODEL.csv")
save_path_meta_robust <- paste0(wd, "/Results/ldsc_hdl_meta_significant_ROBUST.csv")

write.csv(all_results_all, save_path_all_results, row.names = FALSE)
write.csv(sig_model_min, save_path_meta_model,  row.names = FALSE)
write.csv(sig_robust_min, save_path_meta_robust, row.names = FALSE)



### Table Alzheimers
ldsc_main_minor <- ldsc %>% filter((selection_1=="main"|selection_1=="minor")&(selection_2=="main"|selection_2=="minor"))
hdl_main_minor <- hdl %>% filter((selection_1=="main"|selection_1=="minor")&(selection_2=="main"|selection_2=="minor"))

get_disease_matrix <- function(df,
                               target_disease,
                               only_sig = FALSE,
                               source = c("auto", "model", "robust"),
                               alpha = 0.05) {
  
  suppressPackageStartupMessages({
    library(dplyr)
    library(tidyr)
  })
  
  source <- match.arg(source)
  
  # -------------------------------------------------------------------------
  # 1) Decide which columns contain the effect size (rg) and p-value
  #
  # Supported input schemas:
  # - Old schema: rg, p
  # - New comparison schema: model_rg/model_p and robust_rg/robust_p
  #
  # source="auto":
  #   - If robust_* exists, prefer robust (typical for final results)
  #   - Else if model_* exists, use model
  #   - Else fall back to rg/p
  # -------------------------------------------------------------------------
  has_rg_p      <- all(c("rg", "p") %in% names(df))
  has_model_rgp <- all(c("model_rg", "model_p") %in% names(df))
  has_rob_rgp   <- all(c("robust_rg", "robust_p") %in% names(df))
  
  if (source == "auto") {
    if (has_rob_rgp) {
      rg_col <- "robust_rg"; p_col <- "robust_p"
    } else if (has_model_rgp) {
      rg_col <- "model_rg";  p_col <- "model_p"
    } else if (has_rg_p) {
      rg_col <- "rg";        p_col <- "p"
    } else {
      stop("Input df has no usable (rg,p) columns. Expected rg/p OR model_rg/model_p OR robust_rg/robust_p.")
    }
  } else if (source == "model") {
    if (has_model_rgp) {
      rg_col <- "model_rg";  p_col <- "model_p"
    } else if (has_rg_p) {
      # fallback for older inputs
      rg_col <- "rg";        p_col <- "p"
    } else {
      stop("source='model' but no model_rg/model_p (or rg/p) columns found.")
    }
  } else { # source == "robust"
    if (has_rob_rgp) {
      rg_col <- "robust_rg"; p_col <- "robust_p"
    } else if (has_rg_p) {
      # fallback for older inputs
      rg_col <- "rg";        p_col <- "p"
    } else {
      stop("source='robust' but no robust_rg/robust_p (or rg/p) columns found.")
    }
  }
  
  # -------------------------------------------------------------------------
  # 2) Build labels safely:
  # - If label_1/label_2 exist, use them
  # - Otherwise fall back to disease names (so pivot_wider still works)
  # -------------------------------------------------------------------------
  if (!("label_1" %in% names(df))) df$label_1 <- df$disease_1
  if (!("label_2" %in% names(df))) df$label_2 <- df$disease_2
  
  # If selection columns are missing, create them as NA so filters don't crash
  if (!("selection_1" %in% names(df))) df$selection_1 <- NA_character_
  if (!("selection_2" %in% names(df))) df$selection_2 <- NA_character_
  
  # -------------------------------------------------------------------------
  # 3) Normalize to a directed long format:
  # Each undirected pair becomes two rows:
  #   disease_1 -> disease_2 and disease_2 -> disease_1
  # This lets us filter by target_disease as the "column disease".
  # -------------------------------------------------------------------------
  df_long <- bind_rows(
    df %>% transmute(
      d_row = disease_1, l_row = label_1, s_row = selection_1,
      d_col = disease_2, l_col = label_2, s_col = selection_2,
      rg = .data[[rg_col]],
      p  = .data[[p_col]]
    ),
    df %>% transmute(
      d_row = disease_2, l_row = label_2, s_row = selection_2,
      d_col = disease_1, l_col = label_1, s_col = selection_1,
      rg = .data[[rg_col]],
      p  = .data[[p_col]]
    )
  )
  
  # -------------------------------------------------------------------------
  # 4) Filter to the target disease as the "column"
  # Keep only main (or empty/NA) rows on the "row side" to match your prior logic.
  # -------------------------------------------------------------------------
  res <- df_long %>%
    filter(d_col == target_disease) %>%
    filter(d_row != target_disease) %>%
    filter(is.na(s_row) | s_row == "" | s_row == "main")
  
  # -------------------------------------------------------------------------
  # 5) Format cell text
  # - Add star if p <= alpha
  # - If only_sig=TRUE, set non-significant cells to NA
  #
  # NOTE: Use vectorized logic (if_else) to avoid non-vectorized if() inside mutate().
  # -------------------------------------------------------------------------
  formatted <- res %>%
    mutate(
      star = if_else(!is.na(p) & p <= alpha, "*", ""),
      val_text = paste0(
        formatC(rg, digits = 3, format = "f"),
        star,
        " (",
        if_else(is.na(p), "NA", formatC(p, digits = 2, format = "f")),
        ")"
      ),
      val = if (only_sig) if_else(!is.na(p) & p <= alpha, val_text, NA_character_) else val_text
    )
  
  # -------------------------------------------------------------------------
  # 6) Wide matrix: rows are diseases, columns are labels for the target disease
  # (Usually the target disease has a single label, but this keeps your structure.)
  # -------------------------------------------------------------------------
  matrix_final <- formatted %>%
    arrange(d_row) %>%
    select(d_row, l_col, val) %>%
    pivot_wider(names_from = l_col, values_from = val) %>%
    rename(Disease = d_row) %>%
    as.data.frame()
  
  return(matrix_final)
}

alz_ldsc_sig <- get_disease_matrix(ldsc, target_disease = "alzheimer's disease", source = "robust", only_sig = TRUE)
alz_ldsc <- get_disease_matrix(ldsc, target_disease = "alzheimer's disease", source = "model", only_sig = TRUE)

