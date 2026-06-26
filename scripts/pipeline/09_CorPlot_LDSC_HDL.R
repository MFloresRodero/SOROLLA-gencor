## Code developed by Jon Sanchez-Valle
## Barcelona Supercomputing Center
## Life Science Department
## Computational Biology Group
## Email: jon.sanchez@bsc.es


#### Compare the obtained networks with epidemiology by gender ####
library(corrplot)

setwd("/home/maria/git/SOROLLA/Results")

## load the tables ##
corres<-read.csv2("hdl_ldsc_shared.csv",stringsAsFactors = F,sep=",")
tabla<-read.csv2("excell_shared.csv",stringsAsFactors = F,sep=",")

## convert ugly names to beautiful ones ##
nameconvert<-tabla$disease ; names(nameconvert)<-tabla$label
corres$label_1<-as.character(nameconvert[corres$label_1])
corres$label_2<-as.character(nameconvert[corres$label_2])
## convert into 1 those correlations larger than 1, and register them ##
length(which(as.numeric(corres$rg)>1))
corres$rg[which(as.numeric(corres$rg)>1)]<-1

## Get the list of diseases
diseases<-unique(c(corres$label_1,corres$label_2))
diseases<-sort(diseases)
categories<-tabla$type ; names(categories)<-tabla$disease
## Order diseases alphabetically and based on the category they belong to ##
diseases<-diseases[order(gsub("PSY","3PSY",gsub("CAN","2CAN",gsub("NEU","1NEU",as.character(categories[diseases])))),decreasing = F)]
## Create the matrix for the correlation plot ##
cormat<-matrix(ncol=length(diseases),nrow=length(diseases),NA)
colnames(cormat)<-diseases ; rownames(cormat)<-diseases
netmat<-matrix(ncol=length(diseases),nrow=length(diseases),"")
colnames(netmat)<-diseases ; rownames(netmat)<-diseases
corpos<-cormat ; corneg<-cormat

negro<-cormat
for(a in 1:length(negro[,1])){
  negro[a,a]<-1
}

for(a in 1:length(corres$label_1)){
  # a<-2
  if(corres$Software[a]=="LDSC"){
    if(corres$label_1[a]!=corres$label_2[a]){
      if(which(diseases==corres$label_1[a])<which(diseases==corres$label_2[a])){
        cormat[corres$label_1[a],corres$label_2[a]]<-as.numeric(corres$rg[a])
        if(as.numeric(corres$rg[a])>0){
          corpos[corres$label_1[a],corres$label_2[a]]<-as.numeric(corres$rg[a])
        }
        if(as.numeric(corres$rg[a])<0){
          corneg[corres$label_1[a],corres$label_2[a]]<-as.numeric(corres$rg[a])*(-1)
        }
        if(as.numeric(corres$rg[a])<0){netmat[corres$label_1[a],corres$label_2[a]]<-"*"}
      }
      if(which(diseases==corres$label_1[a])>which(diseases==corres$label_2[a])){
        cormat[corres$label_2[a],corres$label_1[a]]<-as.numeric(corres$rg[a])
        if(as.numeric(corres$rg[a])>0){
          corpos[corres$label_2[a],corres$label_1[a]]<-as.numeric(corres$rg[a])
        }
        if(as.numeric(corres$rg[a])<0){
          corneg[corres$label_2[a],corres$label_1[a]]<-as.numeric(corres$rg[a])*(-1)
        }
        if(as.numeric(corres$rg[a])<0){netmat[corres$label_2[a],corres$label_1[a]]<-"*"}
      }
    }
  }
  if(corres$Software[a]=="HDL"){
    if(corres$label_1[a]!=corres$label_2[a]){
      if(which(diseases==corres$label_1[a])>which(diseases==corres$label_2[a])){
        cormat[corres$label_1[a],corres$label_2[a]]<-as.numeric(corres$rg[a])
        if(as.numeric(corres$rg[a])>0){
          corpos[corres$label_1[a],corres$label_2[a]]<-as.numeric(corres$rg[a])
        }
        if(as.numeric(corres$rg[a])<0){
          corneg[corres$label_1[a],corres$label_2[a]]<-as.numeric(corres$rg[a])*(-1)
        }
        if(as.numeric(corres$rg[a])<0){netmat[corres$label_1[a],corres$label_2[a]]<-"*"}
      }
      if(which(diseases==corres$label_1[a])<which(diseases==corres$label_2[a])){
        cormat[corres$label_2[a],corres$label_1[a]]<-as.numeric(corres$rg[a])
        if(as.numeric(corres$rg[a])>0){
          corpos[corres$label_2[a],corres$label_1[a]]<-as.numeric(corres$rg[a])
        }
        if(as.numeric(corres$rg[a])<0){
          corneg[corres$label_2[a],corres$label_1[a]]<-as.numeric(corres$rg[a])*(-1)
        }
        if(as.numeric(corres$rg[a])<0){netmat[corres$label_2[a],corres$label_1[a]]<-"*"}
      }
    }
  }
}
colores <- colorRampPalette(c("#1B4521","transparent","#440F53"))(100)
# colores <- colorRampPalette(c("#1B4521","#8CA190","#987E9F","#440F53"))(201)
# colores[101]<-"white"
pdf(file="LDSC_HDL_corplots.pdf")
  corrplot(cormat, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(-1,1),col=colores,bg="transparent",na.label = " ")
  
  corrplot(cormat, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(-1,1),col=colores,bg="transparent",na.label = " ")
  for(d in 1:length(netmat[,1])){
    numero<-length(netmat[,1]):1
    texto<-netmat[d,]
    text(1:length(netmat[d,]),rep(numero[d],length(netmat[d,])),texto,cex = 0.5)
  }
dev.off()

## Two colors differently ##
colorespos <- colorRampPalette(c("transparent","#440F53"))(100)
coloresneg <- colorRampPalette(c("transparent","#1B4521"))(100)
coloresnegro <- colorRampPalette(c("transparent","black"))(100)

pdf(file="LDSC_HDL_corplots_shapes.pdf")
  corrplot(corpos, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(0,1),col=colorespos,bg="transparent",na.label = " ",method = "circle")
  corrplot(corneg, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(0,1),col=coloresneg,bg="transparent",na.label = " ",method = "square")
  corrplot(negro, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(0,1),col=coloresnegro,bg="transparent",na.label = " ",method = "square")
dev.off()





### Heterogeneity test - depression datasets
mdd <- read.csv("hdl_ldsc_depression.csv")

# Corregir correlaciones mayores a 1
mdd$rg <- as.numeric(mdd$rg)
mdd$rg[mdd$rg > 1] <- 1

# Obtener etiquetas únicas y ordenadas
labels <- sort(unique(c(mdd$label_1, mdd$label_2)))

# Inicializar matrices vacías
cormat <- matrix(NA, nrow = length(labels), ncol = length(labels))
colnames(cormat) <- labels
rownames(cormat) <- labels

corpos <- cormat
corneg <- cormat
netmat <- matrix("", nrow = length(labels), ncol = length(labels))
colnames(netmat) <- labels
rownames(netmat) <- labels

negro <- diag(1, length(labels))
colnames(negro) <- labels
rownames(negro) <- labels

# Rellenar matrices
for (a in 1:nrow(mdd)) {
  l1 <- mdd$label_1[a]
  l2 <- mdd$label_2[a]
  rg <- mdd$rg[a]
  sw <- mdd$Software[a]
  
  if (l1 != l2 && !is.na(rg)) {
    if (sw == "LDSC") {
      if (which(labels == l1) < which(labels == l2)) {
        cormat[l1, l2] <- rg
        corpos[l1, l2] <- if (rg > 0) rg else NA
        corneg[l1, l2] <- if (rg < 0) -rg else NA
        netmat[l1, l2] <- if (rg < 0) "*" else ""
      } else {
        cormat[l2, l1] <- rg
        corpos[l2, l1] <- if (rg > 0) rg else NA
        corneg[l2, l1] <- if (rg < 0) -rg else NA
        netmat[l2, l1] <- if (rg < 0) "*" else ""
      }
    }
    if (sw == "HDL") {
      if (which(labels == l1) > which(labels == l2)) {
        cormat[l1, l2] <- rg
        corpos[l1, l2] <- if (rg > 0) rg else NA
        corneg[l1, l2] <- if (rg < 0) -rg else NA
        netmat[l1, l2] <- if (rg < 0) "*" else ""
      } else {
        cormat[l2, l1] <- rg
        corpos[l2, l1] <- if (rg > 0) rg else NA
        corneg[l2, l1] <- if (rg < 0) -rg else NA
        netmat[l2, l1] <- if (rg < 0) "*" else ""
      }
    }
  }
}

# Paletas de color
colores <- colorRampPalette(c("#1B4521","transparent","#440F53"))(100)
colorespos <- colorRampPalette(c("transparent","#440F53"))(100)
coloresneg <- colorRampPalette(c("transparent","#1B4521"))(100)
coloresnegro <- colorRampPalette(c("transparent","black"))(100)

# Graficar principal
pdf(file = "LDSC_HDL_mdd_corrplot.pdf")
if (any(!is.na(cormat))) {
  corrplot(cormat, is.corr = FALSE, tl.col = "black", cl.cex = 1, tl.cex = 0.7,
           col.lim = c(-1,1), col = colores, bg = "transparent", na.label = " ")
  for (d in 1:nrow(netmat)) {
    y <- nrow(netmat):1
    text(1:ncol(netmat), rep(y[d], ncol(netmat)), netmat[d, ], cex = 0.5)
  }
}
dev.off()

# Graficar formas por signo
pdf(file = "LDSC_HDL_mdd_corrplot_shapes.pdf")
if (any(!is.na(corpos))) {
  corrplot(corpos, is.corr = FALSE, tl.col = "black", cl.cex = 1, tl.cex = 0.7,
           col.lim = c(0,1), col = colorespos, bg = "transparent", na.label = " ", method = "circle")
}
if (any(!is.na(corneg))) {
  corrplot(corneg, is.corr = FALSE, tl.col = "black", cl.cex = 1, tl.cex = 0.7,
           col.lim = c(0,1), col = coloresneg, bg = "transparent", na.label = " ", method = "square")
}
corrplot(negro, is.corr = FALSE, tl.col = "black", cl.cex = 1, tl.cex = 0.7,
         col.lim = c(0,1), col = coloresnegro, bg = "transparent", na.label = " ", method = "square")
dev.off()


## Two colors differently ##
colorespos <- colorRampPalette(c("transparent","#440F53"))(100)
coloresneg <- colorRampPalette(c("transparent","#1B4521"))(100)
coloresnegro <- colorRampPalette(c("transparent","black"))(100)

pdf(file="LDSC_HDL_mdd_shapes.pdf")
corrplot(corpos, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(0,1),col=colorespos,bg="transparent",na.label = " ",method = "circle")
corrplot(corneg, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(0,1),col=coloresneg,bg="transparent",na.label = " ",method = "square")
corrplot(negro, is.corr = F,tl.col = "black",cl.cex = 1.,tl.cex = 0.7,col.lim = c(0,1),col=coloresnegro,bg="transparent",na.label = " ",method = "square")
dev.off()











