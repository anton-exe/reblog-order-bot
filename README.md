# reblog-order-bot
R.O.B. is a Discord bot to help keep track of reblog orders in Tumblr threads.

## Usage
To start a thread, run `rob!start [user] [user] ...`, either pinging or putting the user id of everyone you want in the thread. The reblog order will be based off the order you put everyone into the command. When you send the command, R.O.B. will start a new Discord thread for all the pings.

To change the thread name, run `rob!rename [name]`.

When it's someone's turn, the bot will ping them every 23 hours, in case they were busy during previous pings.

When your turn is done, run `rob!next`. You can also optionally add in a url to your reblog, or pretty much any bit of text you want the next person to see, by doing something like `rob!next https://www.tumblr.com/anton-exe/732451290355040256 PS. remember not to do X! that will mess up my plans`.

If someone already reblogged, but is forgetting to run `rob!next`, you can simply add `force` as an argument to force pass their turn.

To join a thread midway through, run `rob!join [index]`, with the index being where in the order you want to join. (Note: List indices start at **0**. Putting "5" in as the index puts you in the 6th position)

To check the reblog order, run `rob!order`.

Once the thread is done, run `rob!end`.
