library(ggplot2)

df<-read.csv("...") #path

ggplot(data=df,aes(x=k_1,y=bm25_ndcg_cut_10))+geom_point()
ggplot(data=df,aes(x=b,y=bm25_ndcg_cut_10))+geom_point()
ggplot(data=df,aes(x=mu,y=bm25_ndcg_cut_10))+geom_point()
x<-lm(bm25_ndcg_cut_10 ~ k_1+mu+b,data = df)
anova(x)

x<-lm(lm_ndcg_cut_10 ~ k_1+mu+b,data = df)
anova(x)

x<-lm(ltr_ndcg_cut_10 ~ k_1+mu+b,data = df)
anova(x)
