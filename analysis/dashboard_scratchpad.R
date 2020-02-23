library(tidyverse)
library(tidytext)
library(lubridate)

history <- 
  read_csv('transaction_history.csv') %>% 
  mutate(Timestamp = ymd_hms(Timestamp))

history %>% 
  ggplot(aes(x=Timestamp, y=Amount, color=Payee)) + 
  geom_point() + 
  scale_x_datetime(date_breaks = '1 month',
                   date_labels = '%b %y')



  
  
history %>% 
  


