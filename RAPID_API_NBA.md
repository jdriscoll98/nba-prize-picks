Introduction
Welcome to API-NBA! You can use our API to access all API endpoints, which can get information about NBA.

We have language bindings in C, C#, cURL, Dart, Go, Java, Javascript, NodeJs, Objective-c, OCaml, Php, PowerShell, Python, Ruby, Shell and Swift! You can view code examples in the dark area to the right, and you can switch the programming language of the examples with the tabs in the top right.

Authentication
We uses API keys to allow access to the API. You can register a new API key in rapidapi.

The accounts on RapidAPI and on our Dashboard are dissociated. Each of these registration methods has its own URL and API-KEY. You must therefore adapt your scripts according to your subscription by adapting the URL and your API-KEY.

RAPIDAPI : https://api-nba-v1.p.rapidapi.com/

API-SPORTS : https://v2.nba.api-sports.io/

Our API expects for the API key to be included in all API requests to the server in a header that looks like the following:

Make sure to replace XxXxXxXxXxXxXxXxXxXxXxXx with your API key.

REQUESTS HEADERS & CORS

The API is configured to work only with GET requests and allows only the headers listed below:

x-rapidapi-host
x-rapidapi-key
If you make non-GET requests or add headers that are not in the list, you will receive an error from the API.

Some frameworks (especially in JS, nodeJS..) automatically add extra headers, you have to make sure to remove them in order to get a response from the API.

RAPIDAPI Account
All information related to your subscription are available on the rapidApi developer dashboard.

The RapidAPI developer dashboard is where you can see all of your apps, locate API keys, view analytics, and manage billing settings.

To access the dashboard, simply login to RapidAPI and select 'My Apps' in the top-right menu. Alternatively, you can head directly to https://rapidapi.com/developer/dashboard.

In the main dashboard, you will see account-wide analytics and account information. To get more detailed information, you can select tabs on the left-hand side of the screen.

App Specific Analytics
Using the RapidAPI dashboard, you can also view analytics specific to each app in your account. To do so, switch over to the 'Analytics' tab of your application in the dashboard.

On the top of the page, you'll be able to see a chart with all the calls being made to all the APIs your app is connected to. You'll also be able to see a log with all the request data. You are also able to filter these analytics to only show certain APIs within the app.

In each graph, you can view the following metrics:

API Calls: how many requests are being made
Error rates: how many requests are error some
Latency: how long (on average) requests take to execute
You may change the time period you're looking at by clicking the calendar icon and choosing a time range.

Headers sent as response
When consuming our API, you will always receive the following headers appended to the response:

server: The current version of the API proxy used by RapidAPI.
x-ratelimit-requests-limit: The number of requests the plan you are currently subscribed to allows you to make, before incurring overages.
x-ratelimit-requests-remaining: The number of requests remaining before you reach the limit of requests your application is allowed to make, before experiencing overage charges.
X-RapidAPI-Proxy-Response: This header is set to true when the RapidAPI proxy generates the response, (i.e. the response is not generated from our servers)

API-SPORTS Account
If you decided to subscribe directly on our site, you have a dashboard at your disposal at the following url: dashboard

It allows you to:

To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.
You can also consult all this information directly through the API by calling the endpoint status.

This call does not count against the daily quota.

get("https://v2.nba.api-sports.io/status");

// response
{
    "get": "status",
    "parameters": [],
    "errors": [],
    "results": 1,
    "response": {
        "account": {
            "firstname": "xxxx",
            "lastname": "XXXXXX",
            "email": "xxx@xxx.com"
        },
        "subscription": {
            "plan": "Free",
            "end": "2020-04-10T23:24:27+00:00",
            "active": true
        },
        "requests": {
            "current": 12,
            "limit_day": 100
        }
    }
}
Headers sent as response
When consuming our API, you will always receive the following headers appended to the response:

x-ratelimit-requests-limit: The number of requests allocated per day according to your subscription.
x-ratelimit-requests-remaining: The number of remaining requests per day according to your subscription.
X-RateLimit-Limit: Maximum number of API calls per minute.
X-RateLimit-Remaining: Number of API calls remaining before reaching the limit per minute.

Sample Scripts
Here are some examples of how the API is used in the main development languages.

You have to replace {endpoint} by the real name of the endpoint you want to call, like leagues or games for example. In all the sample scripts we will use the leagues endpoint as example.

Also you will have to replace XxXxXxXxXxXxXxXxXxXxXx with your API-KEY provided in the dashboard or on rapidapi.

Python
http.client

import http.client

conn = http.client.HTTPSConnection("v2.nba.api-sports.io")

headers = {
    'x-rapidapi-host': "v2.nba.api-sports.io",
    'x-rapidapi-key': "XxXxXxXxXxXxXxXxXxXxXxXx"
    }

conn.request("GET", "/leagues", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
Requests

url = "https://v2.nba.api-sports.io/leagues"

payload={}
headers = {
  'x-rapidapi-key': 'XxXxXxXxXxXxXxXxXxXxXxXx',
  'x-rapidapi-host': 'v2.nba.api-sports.io'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

Seasons
seasons
All seasons can be used in other endpoints as filters. Seasons are only 4-digit keys like YYYY.

This endpoint does not require any parameters.

header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
Array of objects
errors	
Array of objects
results	
number
response	
Array of objects


Leagues
leagues
Get the list of available leagues.

All leagues can be used in other endpoints as filters.

Available leagues

Africa
Orlando
Sacramento
Standard
Utah
Vegas
This endpoint does not require any parameters.

header Parameters
x-rapidapi-key
required
string
You rapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
Array of objects
errors	
Array of objects
results	
number
response	
Array of objects

Games
games
Get the list of games according to the parameters.

Available status

1 : Not Started
2 : live
3 : Finished
4 : Postponed
5 : Delayed
6 : Canceled
This endpoint requires at least one parameter.

query Parameters
id	
integer
The id of the game

date	
stringYYYY-MM-DD
Example: date=2022-03-09
A valid date

live	
string
Value: "all"
Example: live=all
league	
string
Enum: "Africa" "Orlando" "Sacramento" "Standard" "Utah" "Vegas"
Example: league=standard
The name of the league

season	
integer = 4 characters YYYY
The season

team	
integer
The id of the team

h2h	
string
Example: h2h=1-4
Two teams ids

header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
object
errors	
Array of objects
results	
number
response	
Array of objects non-empty unique

statistics
Get the statistics of the teams that played a game.

query Parameters
id
required
integer
The id of the game

header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
object
errors	
Array of objects
results	
number
response	
Array of objects non-empty unique


Teams
teams
Get data about teams.

The team id are unique in the API and teams keep it among all seasons.

Available conferences

East
West
Available divisions

Atlantic
Central
Northwest
Pacific
Southeast
Southwest
query Parameters
id	
integer
The id of the team

name	
string
Example: name=Atlanta Hawks
The name of the team

code	
string = 3 characters
Example: code=ATL
The shortcode of the team

league	
string
Enum: "Africa" "Orlando" "Sacramento" "Standard" "Utah" "Vegas"
Example: league=standard
The league of the team

conference	
string
Enum: "East" "West"
Example: conference=East
The conference of the team

division	
string
Enum: "Atlantic" "Central" "Northwest" "Pacific" "Southeast" "Southwest"
Example: division=Southeast
The division of the team

search	
string >= 3 characters
Example: search=Atlanta
The name of the team

header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
object
errors	
Array of objects
results	
number
response	
Array of objects non-empty unique

statistics
Get the overall statistics of a team for a given season.

query Parameters
id
required
integer
The id of the team

season
required
integer = 4 characters YYYY
The season

stage	
integer
The stage of the games

header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
object
errors	
Array of objects
results	
number
response	
Array of objects non-empty unique

Players
players
Get data about players.

The player id are unique in the API and players keep it among all seasons.

This endpoint requires at least one parameter.

query Parameters
id	
integer
The id of the player

name	
string
Example: name=James
The name of the player

team	
integer
The team id

season	
integer = 4 characters YYYY
The season

country	
string
Example: country=USA
The country

search	
string >= 3 characters
Example: search=Jame
header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
object
errors	
Array of objects
results	
number
response	
Array of objects non-empty unique

statistics
Get statistics from one or more players.

This endpoint requires at least one parameter.

query Parameters
id	
integer
The id of the player

game	
integer
The id of the game

team	
integer
The id of the team

season	
integer = 4 characters YYYY
The season

header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
object
errors	
Array of objects
results	
number
response	
Array of objects non-empty unique


Standings
standings
Get the standings for a league & season.

Available conferences

East
West
Available divisions

Atlantic
Central
Northwest
Pacific
Southeast
Southwest
Parameters league & season are required.

query Parameters
league
required
string
Enum: "Africa" "Orlando" "Sacramento" "Standard" "Utah" "Vegas"
Example: league=standard
The name of the league

season
required
integer = 4 characters YYYY
The season

team	
integer
The id of the team

conference	
string
Enum: "East" "West"
Example: conference=east
The conference name

division	
string
Enum: "Atlantic" "Central" "Northwest" "Pacific" "Southeast" "Southwest"
Example: division=southeast
The division name

header Parameters
x-rapidapi-key
required
string
Your RapidAPI Key

Responses
200 OK
Response Schema: application/json
get	
string non-empty
parameters	
object
errors	
Array of objects
results	
number
response	
Array of objects non-empty unique