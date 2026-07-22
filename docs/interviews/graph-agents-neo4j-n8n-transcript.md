0:00
AI agents are powerful, but they're missing something critical. They can't see how your data connects together.
0:06
Knowledge graphs solve this problem. And by following along with me step by step, by the end of this video, you'll have
0:12
built your very own custom knowledge graph in Neo4j along with a graph agent in N8N that can intelligently navigate
0:20
complex data relationships. And I know graphs can sound intimidating, but we have a secret weapon, the Neo4j MCP and
0:28
claw desktop. With this, you can literally talk to your graph to make changes, add data, retrieve information.
0:34
So, there's absolutely no need to write custom cipher queries or anything like that. But I'm not stopping there. I'm
0:40
going to demonstrate two highly practical realworld use cases that showcases the true power of knowledge
0:46
graphs and agentic retrieval in N8N. The first is our customer 360 graph agent
0:51
that gives you a complete view of your customer and their interactions with your business. And the second is our
0:56
document structure graph that intelligently navigates complex documents like legal contracts and
1:02
regulations. I've put a ton of work into this one, so I'd really appreciate if you gave the video a like below and
1:07
subscribe to our channel for more AI and NAD content. It really helps us out. Let's get into it. Let's start off with
1:14
a quick explainer on what is a knowledge graph. And essentially, a knowledge graph is a way of storing information
1:19
that focuses on the connection between things. It's a web of interconnected points where each point represents
1:25
something. So here for example I have Emma Williams which is a customer and Emma Williams placed this order. Or
1:32
order number two that order contains a phone case which is a product. So you see these lines in between these points
1:39
and they represent the relationships. So this order contains this product. Emma Williams placed this order. Emma
1:46
Williams raised this support ticket on a product defect. So it is possible to do this in a more relational database. You
1:53
could have a customer table. You could have a support ticket table, an orders table, and then you would use foreign
1:59
keys to interconnect the records in the tables. But knowledge graphs are more flexible. You don't need rigid foreign
2:06
keys. You can draw connections to any entities very easily. And with a property graph like this, these nodes
2:12
and edges or entities and relationships essentially have properties. So you can
2:18
see on the right here, Emma Williams has an email address, a join date, the total
2:23
spend on her account. Or if you look at this order, which contains this phone case. If you click on contains, it shows
2:29
the price is 1999. And one of these phone cases is included in that order. And that's a knowledge graph in a
2:35
nutshell. You have nodes, you have edges, and you have properties. So it is a data store the same as a relational
2:41
database, except it's more like a mind map instead of a spreadsheet. And that makes the connections between nodes or
2:48
entities easier to visualize and then easier to explore. And you can model lots of things in a knowledge graph. So
2:54
here I'm modeling customers and orders and products. But in this knowledge graph I'm actually modeling a document.
3:00
So here we have different chunks and it's a legal document. So we have legal clauses that are included in the chunks
3:06
and everything is then interconnected and related. So you can see here that this text chunk comes from clause 10,
3:13
but it actually references clause 5.2. So that way we can intelligently load up all of the cross references in a
3:20
document. So the way you actually retrieve data and traverse a graph like this is by using cipher which is a
3:26
specialized graph language. So here's an example cipher statement. We're looking to match all of the nodes where the
3:32
customer name is Michael Chen and we want to return the nodes, the relationships, and the other connected
3:38
nodes. And if I copy that in here, paste it at the top and execute, you can see that there we have the Michael Chen node
3:45
and all of the relationships and interconnected nodes. So then to traverse within this browser, you just
3:50
double click. So you can see he placed order 009. If you double click there, that included a phone case, a Bluetooth
3:58
speaker, and a desk clamp. If you click on the phone case, you can see that that was also ordered as part of order number
4:04
two. If we go to this query that he raised and double click it, you can see that that technical issue was about that
4:10
Bluetooth speaker. So, it's easy to visually explore the graph and discover hidden connections that would be
4:16
difficult in flat database tables. But obviously, the barrier to entry here is needing to know cipher to be able to
4:22
query this. And thanks to AI and particularly MCPs, that's no longer a barrier because in this video, I'll be
4:29
showing you how you can set up the Neo4j MCP with Claw Desktop and then just chat
4:34
to your graph. Give me a list of all orders that Michael Chen has placed along with any of the support tickets
4:39
that he's created that are still open. So, it's now using the MCP to go to the graph database first just to get the
4:45
schema and then it dynamically creates the cipher to actually fetch the information. And we can see Michael Chen
4:52
has two orders. And now it's going to check the support tickets. No open support tickets, but he does have two closed tickets for reference. And these
4:58
are the ones that we saw in the graph. So if you are getting started with knowledge graphs, learning cipher is no
5:03
longer a blocker thanks to the likes of Claw Desktop and this MCP. I'll show you how to set this up in a few minutes. An
5:10
important aspect of knowledge graphs is your data sources. Are you extracting structured data from the likes of
5:15
spreadsheets, database tables, software applications or are you processing unstructured data like what you see in
5:22
PDF files, word documents, meeting transcripts, etc. Because as you saw in this knowledge graph, there is a
5:28
dependency on the data being structured. We have all of these properties here. These nodes and relationships are all
5:35
defined. So if you're processing unstructured data, you need to glean the entities and the relationships from the
5:41
text. And nowadays, a lot of that is done using LLMs and AI. And that was the approach taken in my graph rag video on
5:48
this channel where I used light rag to extract out nodes and edges and then carry out a dduplication process before
5:55
uploading to the knowledge graph. I'll be going through examples of both structured and unstructured data sources
6:00
in this video. If you'd like to get a head start and get access to our customer 360 graph agent as well as our
6:06
graph-based context expansion system, then check out the link in the description to our community, the AI
Create Your First GraphAgent
6:12
automators. To create your first knowledge graph, you're going to need a graph database. In this video, I'm going
6:17
to be using Neo4j, which is one of the most popular graph databases out there. Neo4j does have a free cloud plan.
6:24
However, it's not possible to hit this from N8N. So instead, in this video, I'll be self-hosting Neo4j on Alstio,
6:30
which is a fully managed DevOps platform, and it allows you to deploy an application like Neoforj with the click
6:37
of a button. So for that, create an account and log in, and then simply click create a new service on the top
6:42
right, which brings you to this page, and then just search for Neo4j, which is there. Click select. Choose a cloud
6:48
service provider. So I'll just use HNER and their lowest plan, which comes in at $15 a month, and click next. And that's
6:55
pretty much it. You can leave everything else as is and then click create service on the bottom right. And after a couple
7:01
of minutes, your service is up and running as you can see there. And if you click display admin UI, that'll give you
7:06
the link to the admin interface that you can then log into. And it gives you the username and password as well. So really
7:13
easy. Okay, we're connected. Now, there's one change we need to make before we continue, which is we need
7:19
this add-on library called APOC. This essentially allows us to carry out dynamic cipher queries on the graph
7:26
database. So to get this up and running, if you come back into Alstio, click on update config on the software and then
7:32
just paste in the following lines underneath environment. I'll drop these in the video description, but what we're
7:38
doing is just enabling this library. Then you can click update and restart and then that brings back up the containers with that extension enabled.
7:44
You can see there installing plugin APOC. Great. So we now have our graph database set up on Alstio. So if you
7:50
click let's go under the try a new hosted browser. This is a different UI into your graph database but it's quite
7:57
nice to use. So you just need to drop in your details again. So you can get the connection URL from here. So we'll just
8:03
copy that out and then the password is set here. So copy that and then we can
8:08
click connect. Okay. So we are now connected. So at this point now you have your graph database but there's no
8:14
information in it. So if you click this button underneath nodes, that's loading all of the entities on the graph, but
8:19
you don't have any, so nothing's actually showing. The next step is to start loading data into your graph. So for this, we're going to use Claw
8:25
Desktop and the official Neoforj MCP to manage our graph for us. First off,
8:30
install Claw Desktop if you don't already have it. Then go to the official Neo4j MCP repo. I'll leave a link for
8:36
this below. And as you can see, we now have our prerequisites met. We have Neo4j. We have the APOC plugin
8:42
installed. and claw desktop is our MCP compatible client. So, click on this releases link. And from here, you need
8:48
to download the binary of the MCP server. Under the latest release, click assets and then pick the specific server
8:55
for your operating system. I'm using Windows 64-bit. And from there, you'll have a compressed file. And once you
9:01
extract it, you'll have the Neo4j MCP.exe file. So, just copy that out.
9:07
And then just paste in that .exe file here. And then open up Claw Desktop. Click on the burger menu on the top
9:13
left. Go to file settings. Hit developer at the bottom and then click on edit
9:18
config. Now I already have my existing MCP setup here. Edit config brings you
9:23
to this folder with this file selected. So just open this up in notepad. This is your claw desktop config.json. So I've
9:31
just removed my existing one just to show you how this works. So within the GitHub repo, they give you the JSON you
9:36
need to add to this. Copy that out and then paste that in here. And then you just need to fill out your details for
9:42
your particular graph database. We need our address which is this one here. And you can replace the bolt local host
9:48
address with that one. Our username is Neo4j as well as the database name. And the password is what is set in Alstio
9:56
which is here. So you can just copy that, paste that in there. And I'll just add back in my other MCP server for my
10:03
other Neo4j graph database. Okay, that's it. So we'll save that file. And then you just need to close. Now, if we go
10:10
back into file settings and developer, yeah, you should now see your server. And I have my two servers set up here.
10:16
This is the demo one I just created. So, let's start chatting to this database. Now, can you add two test nodes and a
10:23
dummy relationship to my demo graph database? Okay. So, I can see the available instances. It is hitting MCP
10:30
demo. That's the one I created. And let's allow it. Okay. So, it's added the two nodes as well as a dummy
10:36
relationship. So, let's now actually check our graph. come back into the browser and now on the left you can
10:41
already see the labels have shown and if you click on this asterisk there we go there's our test node and if you click
10:47
on the asterisk under relationship you can see the relationship between them excellent now the one thing about Neo4j
10:53
is you only get a single database per installation so what I like to do is
10:58
have an arbitrary parameter called graph ID and that way then I can kind of
11:03
segment the nodes and relationships within the database let's come back into cloud code. Can you delete out that data
11:10
now from my demograph database? And also, can you create a small data set
11:15
representing Game of Thrones entities and relationships, let's say, and can you create a new tag for these nodes and
11:22
edges called graph ID, and let's set it as Westeros. And that way I can have
11:27
different graph IDs for different data sets. Okay, so there's a bit to do there, but this is the beauty of having Claude actually manage your graph for
11:34
you. So, it's deleting the test data first, which is done. And as you can see, that's updated there. And now we're
11:40
not getting any results. And now it's creating a Game of Thrones data set with my graph ID tagging system. So, it's
11:46
creating some houses, locations, characters. Okay. So, let's try it.
11:51
Allow once and have a look at it. Okay. There we go. So, we can see Jon Snow resides at Castle Black, belongs to
11:59
House Stark, which rules Winterfell. House Lannister is an enemy of House
12:04
Stark. So that's how easy it is to get Claude to actually manage your graph.
12:09
And as well as inserting data like this, it can also update. So let's just pretend Jaime Lannister marries Sansa
12:15
Stark. Can you create a connection between Jaime Lannister and Sansa Stark because they just got married. So it's
12:21
written the cipher query. And now let's have a look. Jaime Lannister, Sansa
12:26
Stark, and they're both married. So that's how you can update your graph just by using your voice. And the fact
12:32
that we have graph ID now set to Westeros. If I come into Claude and I ask it, can you create a data set
12:38
similar to this but now for the Witcher and give it the graph ID the Witcher.
12:43
Now you can click always allow and then that'll set it within the session that it'll automatically execute these cipher
12:49
queries. I prefer to actually see what it's doing though because it has master access to the graph. It could delete
12:54
everything if a request was misinterpreted. So, it is nice to actually sanity check the queries. I'm
13:00
not a cipher expert, but it is quite readable what it's actually doing. So, I've approved that and it has executed
13:06
it. And there we go. We have our factions and locations. Now, when I refresh this, I'm not actually seeing it
13:12
all. And it's because the limit at the top is set to 25. So, let's just set that to 1,000. And then you can run it
13:17
again with this button. Okay. So, we now have our two subgraphs within our database. This one is Game of Thrones.
13:24
This one is The Witcher. So now what you can do is start filtering within the browser. And this is where you can ask
13:30
cloud to create queries for you. Can you provide me a query to use within the Neo
13:35
Forj browser where I can pass in the graph ID and get back all nodes and
13:40
relationships and it gives you the cipher query. So you can just copy that out and then up here we'll paste it in
13:47
and it has Westeros set as the graph ID. So now if I run that now I'm only getting the Westeros ones. House
13:53
Baratheon's off on its own here for some reason. But if I swap this out now to the Witcher and run it again now,
13:59
nothing returned because it's actually uh all lowercase with no space. And there we go. There's the Witcher. And we
14:06
have a couple of isolated nodes. And I think probably what happened was the relationship wasn't actually tagged as
14:11
the Witcher and that's why they're shown as isolated. But that's something that we could get Clawed to fix up and that's
14:17
why it is worth looking at the queries that it's creating. Now the other thing you can do is save these queries. This
14:22
button to the left of the run query is to save the prompt. So let's call this one the Witcher graph. We can save that.
14:28
And then that shows up in the saved cipher list. So you can collect all of these queries that you use to navigate
14:35
and inspect the graph. That way you don't have to go to claude to create the cipher each time or you don't need to
14:41
learn cipher to be able to write it. And I already have quite a lot of saved cipher queries that I'm actually running
14:47
here. We now have our graph database. We've loaded in data using claw desktop and the Neo4j MCP. So now how do we
14:55
create our graph agent? How do we hook this up to NADN? If you go to your NADN instance and let's actually just chat
15:01
the data first. So let's click on add first step and we'll add a chat trigger and then we'll add an AI agent. We'll
15:07
choose a chat model. Again I'll go with Antropics 4.5 sonnet which is pretty good at creating cipher queries. And
15:13
when it comes to communicating with your graph database, there are a few options. So there is no official Neo4j node in
15:20
N8N. However, there is a community node that you can use. So I have that installed here. And the way you actually
15:26
install that, let me just show you. You go to your settings and then go to community nodes. Now I believe this only
15:32
works on self-hosted N8N. You can just click on install on the top right and then you just need to find your
15:38
community node. So click on browse. You just type in Neo4j and click search. And there are a few of these packages
15:45
available. I'll use the one that has the most downloads, which is this one. And then you're simply just copying out the
15:50
actual name of the repo. So, nitnodes- neo4j. You drop that in there, agree to
15:56
the terms and conditions, and click install. And then that will install that community node in your instance, which
16:02
then means you can add this node as a tool to an agent. And then you need to create a credential, which is the same
16:07
as before. You just drop in your connection URI, the username and password, and the database. Click save.
16:13
And then for this tool, let's just give it a resource which is the graph database. And we'll allow it to maybe
16:19
execute a query. Index name is irrelevant because it's not a vector database. And for the cipher query,
16:25
we'll just let the AI populate this. Okay. So, I don't have a system prompt set yet, but uh let's just try it. So,
16:31
let's say tell me about the Witcher. See, can claude figure it out? And it sure can. Yeah. Let's hit the execute
16:37
query. And we do have some nodes coming back. Okay, here we go. Based on the
16:42
database, here's a comprehensive overview of The Witcher. We have our main characters, there's Yennefer, the
16:48
political landscape, there's CRA, and the various locations. And you can see from that tool call then that we have
16:55
got the various responses which are the nodes. And you can see the cipher queries then on the left. So it's
17:00
figured out the graph ID equals the Witcher without me even saying it, which is brilliant. Okay, so that is how you
17:05
create your graph agents. This AI agent can now execute arbitrary cipher commands based off text prompts within
17:13
N8N. And now of course this is just a test. It's dummy data. But the fact that it can execute arbitrary queries is both
17:20
great and very dangerous because it could delete everything in your graph. So two ways around that then would be to
17:26
create a readonly user. So when you're creating your connection here, you're using a different username, not the root
17:32
username along with that user's password. Or the other approach would be to create prepared statements. So if we
17:38
come back into this execute query and instead of allowing the AI to generate the full query, we could delete that
17:44
out. And here then you could paste in a query that either you write or the AI writes. And from here then you could
17:49
drop in different parameters. So let's say you want the AI to actually fill out whether it's the Witcher or Westeros. So
17:56
you drop that in here. So it's from AI graph ID and then you can describe
18:01
choose either the Witcher or Westeros. Okay. And now if we try it again, give me information on Game of Thrones. And
18:08
now it's executed that query, but it's now not an arbitrary query. It's only actually populating the graph ID. It's
18:14
so it's a fixed prepared statement essentially. Now the query returned empty results. So maybe I got the graph ID wrong. Yeah. So it's Westeros with a
18:21
capital W. Okay, we'll try it again. Yeah, and it has come back with data now. Okay, there we go. Major houses,
18:27
key relationships, key locations. Job done. And there's your graph agent. The next question then is how do you load
18:33
data into your knowledge graph because this is how we are querying a graph that already has data that we use claw
18:40
desktop to inject but knowledge graphs need to be constantly fed new information and that's where NADN is
18:45
brilliant because it's an integration platform. So in the use cases I'll be going through I'll show you some
18:50
ingestion flows where we're actually injecting data into graphs. I've got two really interesting use cases here for
Customer360 GraphAgent
18:56
graph agents. The first is a customer 360 graph that provides a single view of
19:02
a customer for a business that an AI agent can interrogate. And the second is a document navigation graph. And this is
19:09
really useful for highly formal legal documents where legal clauses for example need to be linked to definitions
19:16
or footnotes or appendices. So first up our customer 360. And when you think about customer data in the context of a
19:23
business, customer data can be stored in lots of different systems depending on the context. So an e-commerce system
19:29
like Shopify may hold all of the customers online orders. The likes of Zenesk may hold all of the support
19:35
tickets. Maybe there's a CRM that handles all of the leads or opportunities with that customer. And
19:41
then maybe the likes of Stripe holds all of their payment information. So you have all of these disperate isolated
19:47
data silos. And there's huge benefits to actually having a single view of that customer data, both from a business
19:53
intelligence perspective, but also for the likes of an AI agent to interrogate that to help staff support that customer
20:00
with their queries or to extract out more revenue from that customer based off insights. To give you an example of
20:05
how this would work, I've created this knowledge graph using dummy data for customers, orders, products, and support
20:12
tickets. And we have different relationships as well. So for customers, they can place orders. They can raise
20:18
queries. Orders can contain products and support tickets can be about specific
20:24
products. As you see here, I had Claude generate this test data set and create
20:29
CSV files for me to import. These are the nodes and these are the edges. And
20:35
back to earlier when I described structured versus unstructured data sources, these are structured data
20:40
sources. So if you look at the nodes, we have support tickets for example with ticket ids, statuses, priorities,
20:47
categories. And if you look at the edges, we have a table linking tickets to customers. So this type of format is
20:53
very common in a relational database, which is what most of these types of software applications will be using to
21:00
keep track of customer information. The key thing when building a single view of a customer within a knowledge graph then
21:06
is how do you model the data? And while knowledge graphs are more flexible than relational databases, we need to make
21:12
sure that we're matching on a common customer ID, for example, a common support ticket ID, product ID, etc. And
21:19
your data model would evolve as you add more systems and bring in more information. So this is what this data
21:26
model would look like as things stand with these four entities and these four
21:31
types of relationships within N8N. We then need to be able to load this data into the graph. And this can be a
21:38
one-off batch load of all data, but then it also needs to drip feed updates and changes. And as I mentioned, the beauty
21:44
of NADN is that it's highly integrable. It has lots of connectors to different
21:50
software packages, and you can use common HTTP request nodes to hit APIs of
21:55
other packages. So here, for example, we're bringing in support tickets, products, customers, and orders. And
22:01
because I'm using dummy data, I've just uploaded those CSV files to Google Drive. I'm looping through the files,
22:08
downloading them, extracting them, and then injecting them into a query that can be uploaded to the knowledge graph.
22:15
But if you were doing this for real, you would be hooking up all the various different software packages to extract
22:21
out the data and injected into the graph. And the same goes then for the relationships. So if a customer creates
22:28
a ticket, you want that represented in the graph as well. So let's go through this ingestion flow end to end. At the
22:34
moment, it's a manual trigger. you would more likely have that running on a schedule. There's a one-off creation of
22:39
indexes in your graph database. So, I wouldn't necessarily include that in this flow if it was running every time,
22:46
but essentially we're just indexing on the customer ids and the graph IDs here. Here, we're searching for our files and
22:52
folders. And that could also be a solution as well because you could have batch extracts from different software
22:58
packages that dump files into a Google Drive folder and then this type of flow would work perfectly fine. So then you
23:04
loop over the items. We download the CSV file here. We're extracting it. So
23:09
turning it into JSON essentially. And then we inject it into a cipher query
23:15
template. So let's take customers for example. Now again I got Claude to generate this for me. But essentially
23:20
what it's doing is it's taking all of the customers that I'm sending in from the CSV and it's creating them on the
23:26
graph passing in all of the properties of that customer. So it's a simple enough cipher statement. And with that
23:33
query generated, we then just upload it to the knowledge graph. So essentially what we're doing is we're hitting this
23:40
URL and we're hitting the transaction commit endpoint and then we're passing in the query and away you go. And as I
23:46
mentioned, there's lots of different ways that you can integrate with Neo4j in NAND. Previously, I showed you using
23:52
the NAND community node, but you can just hit the API as well as I'm doing here, but the community node would work
23:58
perfectly fine, too. And the other thing is you can use a Neoforj MCP within N8N as well. So lots of different ways you
24:05
can achieve the same thing. And then once the nodes are uploaded, you then create the relationships and it's the
24:10
exact same process. We search the relationships or the edges folder, process the files, generate the queries
24:17
here. Now we're generating the placed query. So the customer places an order. We're passing in the customer ID and the
24:23
order ID. And that's what creates that connection between those nodes. And
24:29
again, just goes straight into that transaction commit endpoint into that specific database and with the
24:35
authentication provided, it's sending in the query. So, this isn't text to cipher. This isn't an AI dreaming up a
24:42
cipher query that may or may not work. We have prepared queries that we're just injecting data into. So, once you set
24:49
this up once, this should work every time. So, using this data loader, I was able to create and generate this graph.
24:56
And with that running on a schedule and with these files being archived into an archive folder, when a new file is
25:02
dropped in, it could be processed and the graph updated. So then on to retrieval, how do you actually chat to
25:08
this graph? Well, there's different user interfaces that you could have here. At a very basic level, you could have a chat endpoint. So here we have our open
25:15
chat. As I mentioned, you could use the Neoforj MCP as well as the API. And just so you know, the MCP here isn't the
25:22
official MCP. We could use that, but instead I'm executing this npm package.
25:27
So, this can essentially run on the fly and it's using the NAN MCP community node. After playing with this, I don't
25:34
actually recommend this because it's quite slow to run. So, I would more likely just use the community module or
25:39
just hit the Neoforj API directly. So, let's disconnect these for the minute. Tell me what orders Sarah Williams has
25:46
created and what support tickets she has. So, that question has gone to the graph agent. It's hit the API and within
25:53
this tool again, we're just hitting the transaction commit URL endpoint and we're allowing the AI to create an
25:59
arbitrary cipher statement. And interestingly, uh, yeah, Sarah Williams doesn't exist. There's an Emma Williams
26:05
and a Sarah Johnson. I completely forgot. Let's go with Emma Williams. So, that's a good example of the AI thinking
26:11
on its feet there. So, it's hit it a couple of times, and this is your standard text to cipher queries. Now
26:17
it's passing in the query the exact same way that Claude would do in Claw Desktop when it's using the MCP. And here we go.
26:24
We found the information. Emma Williams, she's a platinum customer. Total spend is there. And these are the orders and
26:30
these are the support tickets. So what's interesting is you could just have your
26:35
different data silos connected as tools. You could have a CRM, you could have a
26:41
payment gateway, you could have an e-commerce store. And then by asking that question, tell me what orders and
26:47
support tickets, it could hit the different tools to get the result. So an agent can do this without a knowledge
26:53
graph. It's just that using a knowledge graph, number one, makes things a lot faster because there's only a single
26:58
source that you need to traverse and retrieve from. Number two, it makes things more accurate because you have to
27:03
normalize across the different data sources. So if there was conflicting information in different data sources,
27:10
that would possibly be flagged when you come to consolidate the data in the knowledge graph. And number three, you
27:15
can generate hidden insights that would take a huge amount of time to figure out just by looking at the flat tables
27:21
within different systems. For example, if there was a shortage on a particular material that was going into building a
27:26
product, you'll be able to figure out what impact that has on the lead time of customer orders that may be
27:33
forwardplaced for a month's time. So that's quite deep business intelligence that a knowledge graph can actually
27:39
enable. And I mentioned how you can have different interfaces for this. Another interface could just be autodrafting
27:45
responses to emails or support tickets. So here, for example, it could be an email that was received from Sarah
27:51
Johnson asking when will my latest order arrive. And with that executing, that can then hit your knowledge graph, which
27:58
has a copy of all of the data from the individual systems to be able to return the accurate response. And that is then
28:04
drafted this email to Sarah with information about the order, in which case the latest order was actually
28:10
delivered. So it doesn't need to be emailed. Now, this could be in a help desk like Zenesk or Freshesk where maybe
28:16
you draft a response for your agent. So that way they don't have to go digging through the files to figure out where
28:21
the order actually is. Onto our second use case, which is a document navigation graph. And as I mentioned, the example
Document Structure GraphAgent
28:28
here is a highly structured document. Think of legal documents, regulations where there's a lot of cross-
28:34
refferencing of different clauses and different sections and subsections to different definitions or appendices and
28:40
actually providing comprehensive and accurate answers on these types of documents can be incredibly difficult. I
28:46
was inspired by this article on medium which describes this type of solution which is used in a multigraph
28:52
multi-agent recursive retrieval system through legal clauses. So, I've built a
28:57
version of this in N8N. And this was also a topic of my last video where I go through the idea of context expansion
29:04
where the system can extract out a document's inherent structure based off markdown. And then an agent can
29:10
intelligently retrieve different chunks from different sections depending on what content it's getting back from the
29:15
vector store. And what this looks like in reality is an AI agent that should be able to answer questions on a document
29:22
like this, a formal legal document with different article numbers and clauses.
29:28
And if you take this example article which is 610, you can see that the text is cross referencing the article 628. So
29:35
if the AI agent was answering a question on this and it retrieved this back as a chunk, it should also be able to get the
29:42
information from this to formulate a comprehensive answer. And that's what the context expansion solution is aiming
29:48
to solve. But the difficulty with context expansion is it's relying on the structure of the document and
29:54
specifically headers. So while this would show up as a header, article 6.10
30:00
or article 6.28 would not. This is what the interconnected document graph looks
30:05
like. So we have our document in the middle which is then linked to different sections and subsections. Everything you
30:12
see in blue here represent chunks of information and everything in green are
30:17
the clauses, the legal clauses within this document. And from a relationships perspective, you can see that clause
30:23
4.1m is in chunk 105. But then also chunk 116 references clause 4.1m. So if
30:32
chunk 116 was retrieved by a vector store through this graph, you could automatically load up clause 4.1m and
30:40
give a comprehensive answer. This type of graph then requires two distinct stages. The first one is importing the
30:46
document based off the structure of the document, the headings within it. The second then is the enrichment of the
30:52
graph. It's trying to link up those references within those chunks to the different subsections within the
30:58
document. And once the graph is imported and enriched, it can then be retrieved by an agent to formulate accurate
31:05
answers. And this is what the graph-based context expansion looks like. So we have our document, the F1
31:11
financial regulations that we imported. We use Mistral OCR to extract out that
31:16
document's markdown and that document structure. Our system uses Subabase to import the documents because we use that
31:23
as a vector store as well. We then go to an LLM to enrich the document itself. So, in other words, extract out a
31:29
document summary. And then based off my last video, we use our smart chunker and
31:34
our document hierarchy extractor to extract out the index of the document
31:40
based off the heading levels. And this is what that hierarchy looks like. And you can see it's quite detailed except
31:46
it's not going down to the clause by clause level that this type of formal legal document would require. But it
31:53
still works very well for the vast majority of documents. So then what I did is I transformed this hierarchical
31:59
index into graph nodes and edges in this function. So we can see now we have all
32:05
of our graph nodes 250 of them and edges 475 of them. So this now represents the
32:12
different sections and the linkages from a hierarchy perspective and we can save that in the graph and that's pretty much
32:18
what this looks like. So we have our main document. We have the different chunks and the different sections. And
32:24
this one is our definition section which is a large section of the back of the document and it has a lot of chunks
32:30
associated with it. But what's missing is the references that are buried in those chunks to other sections of the
32:35
document. And that's where the enrichment comes in. The approach I took to graph enrichment was to load up all
32:41
of the sections and chunks from the graph. Again, this is just a cipher query. I could have got this from
32:46
Superbase as well, but it's a cipher query that's fetching all of the sections, all of the chunks, and then we
32:52
go through each chunk. And what I'm doing is I'm going to an LLM to actually extract out search terms that I can go
33:00
to the vector database to try to find relevant sections to link to this chunk. So here, for example, we have a chunk
33:07
which is article 628, which is about the complaints procedures. And yeah, it actually references article 8. You can
33:13
see it right there on screen. So the idea then is because this chunk which is in article 6 is referencing article 8,
33:20
it has extracted out article 8 as a search query that we can run against our
33:25
hybrid search system. So then we work through this. We generate embeddings for each of those search queries. We trigger
33:32
hybrid search a large number of times as you can see but superbase hybrid search is well up for it. And back to that run
33:38
eight of 21. So we passed in article 8 as the search into this hybrid search system and it has pulled out the exact
33:46
article eight categories of breach and then that goes to an LLM to glean the
33:51
references. In other words to consider the results that it got from this hybrid search and make a judgment call as to
33:57
whether that actually is a cross reference or not. So if we come in here go to 8 of 21 and actually that is it
34:04
there. So you can see it's chunk index 93 article 8 categories of breach. So
34:10
it's outputed this index 93 as a reference for this chunk that it's processing and then it's enriched in the
34:16
graph with that using this cipher query here. So let's now see what that looks like in the graph. So we're looking for
34:22
chunk index 70 which is this one here. Chunk index 70. And as you can see it references chunk 93. And you can verify
34:29
all of this by looking at the content of this chunk. and that mentions article 8
34:35
and then this reference to chunk 93 if we open it up we can see this is article 8 categories of breach so I think that's
34:42
a brilliant example of dynamic interlinking of sections within a document and that's a great example of
34:49
graph enrichment it's where you're actually putting lots of processing power against enriching the graph so
34:56
when it comes to querying that graph then you could be super fast you don't need an LLM to reason over the structure
35:02
or traverse or do whatever it needs to do. You can just automatically load up all connections of that chunk. The
35:09
downside obviously is the time it takes and the cost of actually enriching it.
35:14
So for this one document like we hit hybrid search 1,100 times. We met around
35:19
400 LLM calls. This took around 16 minutes for a 50-page document. So it's
35:24
not something that I would be doing at scale. I think the context expansion solution I put out in the last video is
35:31
the solution to use at scale. But if you have a really tight use case where you need highly accurate responses for
35:38
highly complex and interlin documents, this is a great approach. So then when it comes to chatting to this document,
35:44
of course you can just load up the full document. I won't show that because you could do that without a knowledge graph.
35:49
But let's look at the neighbor and references retrieval and let's use that example that we found. So chunk 70 is
35:56
about the complaints procedure. Let's ask what's the complaints procedure if there's a sanction for an overspend
36:02
breach. Okay. So that's gone to the vector store and it's retrieved three results and it's got the neighboring
36:08
chunks of those results. Okay. And it has formulated an answer which looks pretty detailed. Let's just check to see
36:14
exactly what happened. So it sent in the complaints procedure a query run one of
36:19
three. So what are we looking for? We're looking for chunk 70 which is actually this one. chunk index 70 and so that was
36:25
the top result. This get neighbor chunks tool is passing in chunk index 70 in
36:30
this case. It's looking for a window size of three. So the three nodes before and the three nodes after following the
36:37
next relationship. So you can see the next relationship is there. So there's chunk 71. Next is chunk 72 obviously and
36:45
it goes backwards as well. And then it also gets any references. So you have references here for example. And then
36:51
based off that additional context, it can answer the question. So the same then goes for section and parent
36:57
references. Instead of following the next relationship, you're following the has child relationship. So we'll ask the
37:03
same question. We get the chunks back from the vector store again. Chunk index 70 is returned. And then we hit this
37:09
endpoint which provides 20 chunks back. We pass to the chunk index 70. And we're
37:15
getting everything from that section. So you can see chunk index 66
37:20
67 and so on and so forth. And then onto smart document traversal. This isn't
37:25
using pre-cooked statements like we have here these prepared statements. Instead it's just text to cipher. So the agent
37:32
can figure out which direction it wants to go in the graph to answer the question. So again back to superbase got
37:39
our chunk index and you need the vector store to actually find a starting point on the graph to traverse from it then
37:46
went to get the graph schema so that it understands the nodes and relationships because we haven't provided it any
37:52
example and then it's able to generate these queries on the fly exactly the same as claw desktop and there's the
37:58
full answer again with this text to cipher version you would want to lock down the actual account because you
38:04
don't want to give someone delete access to the graph. But that in a nutshell is
38:09
smart document traversal using a graph and is ideal for highly structured and
38:14
highly complex documents where you need high levels of accuracy. If you'd like to get access to our graph-based context
38:21
expansion as well as our customer 360 graph agent, then check out the link in the description to our community, the AI
38:27
automators, where you can join hundreds of fellow builders all looking to leverage AI to improve their businesses
38:34
and further their careers. I hope you enjoyed this video. It was a lot of fun actually playing around with knowledge graphs in N8N. I'd really appreciate if
38:41
you gave the video a like below and subscribe to our channel for more deep AI and NAN content. See you in the next
38:47
one.