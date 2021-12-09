library(data.table)
library(ggplot2)
library(h2o)
library(caret)
library(ROSE)
library(e1071)
library(GGally)
library(ggpubr)
library("dplyr")

theme_set(theme_pubr())
h2o.init(nthreads = -1)  #-1 uses all cores

data = fread('parsed_pgn.csv')
data = data[complete.cases(data), ]
summary(data)

# Filtering data with games that have a black player and white player rating lower than 2200 as they would have a lower chance of definitively defining a critical position  with long thinks
data = data[(data$WhiteElo >= 2200 & data$BlackElo >= 2200),]


# Taking a few features from the parsed data that can be useful in determining effective parameters for determining critical position
data = subset(data, select=-c(play_no, game_type, game_id, player, play, clock_timer, time_remaining,
                              game, WhiteElo, BlackElo, Result, RatingDiff, elapsed_time, possible_captures, possible_moves))


set.seed(123)

#---------Removing low correlation columns----------------
data$critical_position = as.numeric(data$critical_position)
correlation = cor(data)
correlation
#data = subset(data, select=c(no_moves, critical_position))
summary(data)

#--------Undersampling-----------------
data = ovun.sample(critical_position~., data = data, method = "under", N = 109883*2)$data

table(data$critical_position)


#------Modelling-------------
data$critical_position = as.factor(data$critical_position)

training = createDataPartition(y=data$critical_position, p=0.80, list=FALSE)

train_set = data[training,]
test_set = data[-training,]


#-------Decision Tree-----------------
decision_tree = train(data=train_set, critical_position~., method='rpart')
d_tree_pred = predict(decision_tree, newdata=test_set)
confusionMatrix(d_tree_pred, test_set$critical_position)

#----------KNN------------------
knn = train(data=train_set, critical_position~., method='knn')
knn_pred = predict(knn, newdata=test_set)
confusionMatrix(knn_pred, test_set$critical_position)
#-------------------------------------

#----------Bagging------------------
bagging = train(data=train_set, critical_position~., method='treebag')
bagging_pred = predict(bagging, newdata=test_set)
confusionMatrix(bagging_pred, test_set$critical_position)
#-------------------------------------

#----------RF------------------
rf = train(data=train_set, critical_position~., method='rf', prox=TRUE)
rf_pred = predict(rf, newdata=test_set)
confusionMatrix(rf_pred, test_set$critical_position)
#-------------------------------------

#----------Log Reg------------------
glm = glm(data=train_set, formula=critical_position~., family=binomial)
glm_pred = predict(glm, newdata=test_set, critical_position = "response")
confusionMatrix(as.factor(glm_pred), test_set$critical_position)
#-------------------------------------

#----------Boosting------------------
boosting = train(data=train_set, critical_position~., method='gbm', verbose=FALSE)
boosting_pred = predict(bagging, newdata=test_set)
confusionMatrix(boosting_pred, test_set$critical_position)
#-------------------------------------

#----------Naive Bayes------------------
nb = train(data=train_set, critical_position~., method='nb')
predict_nb = predict(nb, newdata=test_set)
confusionMatrix(predict_nb, test_set$critical_position)
#-------------------------------------


#-----------------Plotting--------------------------

ggpairs(data)

boxplot(data, main='Multiple Box plots')

data$critical_position = as.factor(data$critical_position)
data$critical_position = ifelse(data$critical_position==1, 'C','NC')




#------------No_moves_KD_plot-----------------------
a = ggplot(data[, c('no_moves', 'critical_position')], aes(x = no_moves))
mu = data %>% 
  group_by(critical_position) %>%
  summarise(grp.mean = mean(no_moves))

a + geom_density(aes(fill = critical_position), alpha = 0.4) +
  geom_vline(aes(xintercept = grp.mean, color = critical_position),
             data = mu, linetype = "dashed") +
  scale_color_manual(values = c("#868686FF", "#EFC000FF"))+
  scale_fill_manual(values = c("#868686FF", "#EFC000FF"))

#------------No_captures_KD_plot-----------------------
a = ggplot(data[, c('no_captures', 'critical_position')], aes(x = no_captures))
mu = data %>% 
  group_by(critical_position) %>%
  summarise(grp.mean = mean(no_captures))
a + geom_density(aes(fill = critical_position), alpha = 0.4) +
  geom_vline(aes(xintercept = grp.mean, color = critical_position),
             data = mu, linetype = "dashed") +
  scale_color_manual(values = c("#868686FF", "#EFC000FF"))+
  scale_fill_manual(values = c("#868686FF", "#EFC000FF"))



          