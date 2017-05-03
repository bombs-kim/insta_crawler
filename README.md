# What is Scrapy?


It is an open source framework for extracting data you need from websites(This is called web crawling). When you do crawling, you are likely to spend more time on waiting for your requests than on actually processing the data. Let's say you have to send many requests for some websites to crawl information at the same time, you may come up with generating many threads(something like virtual CPUs). This is an bad idea becuase almost all the threads do is just waiting for responses.


This is where Scrapy comes in handy. Scrapy doesn't wait once it makes an request but it starts a new request right away, instead. This implies that you can do the same job of making hundres of requests at the same time with only one thread. This is what they say asyncrhonous programming. This kind of program can be written with python neatly with the help of one of Python's great powers, a generator. Read through the scrapy's source code, and you will be amazed by how far a generator can go.




# What is this project about


This is an web crawling project targeted to South Korean users on the Instgram. The most popular SNS among people is Facebook, but it not good for getting information about people's daily activities any more because it's now more of an alternative media for news. On the other hand, people started to use Instagram more often to share their daily lives. Instgram is a great source to get a glimpse of what's trending at a time point.


In the past Instagram provided outsiders with APIs for this purpose but they no longer do that. That's why I started this new project. With the two crawlers of this project, you can start with initial a few usernames and extend it 3 million people which covers most of the Korean users. You can crawl more than 10 million posts in a day with some fine commerical server used.


Even though most code was written by me, this project has been done with another member. This github repository and documentation itself are done by myself. 



# How is this project composed


This project is divided into two main crawlers. First one is user\_crawler, which takes a list of commented posts as an input and then check if they are Korean and add them to the user list. The other one is post\_crawler. It crawls posts of the Korean users found periodically.


## user\_cralwer

user\_crawler has two spiders which are new\_user\_crawler and new\_user\_crawler\_ajax. They essentialy do the same job. new\_user\_crawler starts with a list of commented posts, which comes from post\_crawler. It checks if a user is Korean or not with somewhat naive and conservative approach. If a user's first few posts contains more than a certain number of Korean characters and proportion of Korean is large enough, he is decided to be Korean. new\_user\_crawler also keeps the original list of Korean users it can identify if a username is new or not. When it finishes it returns a list of Korean users newly added.


Also, I figured out a part of the Instgram's communication mechanism between the remote server and the browser and came up with a proper AJAX requests that I can use to customize responses.

```
headers = {'x-csrftoken': key, 'referer': self.baseurl % username}
data = {
    'q': 'ig_user(%s) { media.after(9379061665064369409, 12)'
    ' {\n  nodes {\n    caption,\n    code\n  }\n}\n }' % user_id}

req = FormRequest(
            'https://www.instagram.com/query/',
            headers=headers,
            cookies={'csrftoken': key},
            formdata=data,
            callback=self.parse_profile_page,
            dont\_filter=True,
            meta={
                'cookiejar': response.meta['seq'],
                'username': username,
                'user_id': user_id} )
yield req
```
This part of the code makes an valid AJAX request to the instgram server. With this spider the crawler process becomes almost 10 times faster becuase there are not much overhead in their payload.


## post\_crawler


It only has one spider called post\_spider. It starts by making requests to Korean users you have. The actual information about post like captions, tags and image source is contained in JSON format in the response. First, you need to extract JSON part of the response using builtin scrapy's xpath support. JSON parsing was implemented in `json_helper` module, but for now JSON parsing is done by another module for some akward reasons.




# Disclaimer


I started this project as I started learning Python. The sytle is ugly in that camel case and snake case notations are mixed, the code is not moduled well but just put into few files, and bad names were used, for example, some log files shouldn't be called log because they are used as an valid input for another iteration. Also, it doesn't follow the scrapy's convention. Output are better be output by using builtin feed\_export, not by writing to a file directly. Also, some crawlers should have been named spiders becuase crawlers and spiders indicate different things in scrapy. Not a great work indeed. But this project does its job fine indeed without causing severe errors, to my relief.