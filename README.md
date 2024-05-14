### What is this?
Base is a daemon for linux that continuously monitors and stores what you are doing on your computer. This way, pull statistics, visualize how you spend your time, attach a model to be a semantic memory store, and more. It is inspired by the [Quantified Self](http://en.wikipedia.org/wiki/Quantified_Self)-movement and [Stephen Wolfram's personal key logging](http://blog.stephenwolfram.com/2012/03/the-personal-analytics-of-my-life/) asa well as [SelfSpy](https://github.com/selfspy/selfspy).

See Example Statistics, below, for some of the fabulous things you can do with this data.
### Installation

To install Base, follow these steps:

1. Clone the Base repository:
   ```
   git clone https://github.com/Alignment-Lab-AI/Base.git
   ```

2. Navigate to the Base directory:
   ```
   cd Base
   ```

3. Run the installation command with sudo:
   ```
   sudo make install
   ```

   This command will create the necessary directories and symlinks:
   - It creates a `/var/lib/Base` directory and installs the Python files from the `Base/` directory into it.
   - It creates a `/usr/bin` directory if it doesn't already exist.
   - It creates symlinks in `/usr/bin` for the `__init__.py` and `stats.py` files, making them accessible as `Base` and `Baseview` commands respectively.

   Note: The installation destination can be customized by setting the `DESTDIR` variable when running `make install`. For example:
   ```
   sudo make install DESTDIR=/path/to/custom/directory
   ```

4. After installation, you can run Base using the `Base` command and view statistics using the `Baseview` command.

That's it! Base should now be installed on your system and ready to use.



### Running Base
You run Base with `Base`. You should probably start with `Base --help` to get to know the command line arguments. As of this writing, it should look like this:

```
optional arguments:
  -h, --help            show this help message and exit
  -c FILE, --config FILE
                        Config file with defaults. Command line parameters
                        will override those given in the config file. The
                        config file must start with a "[Defaults]" section,
                        followed by [argument]=[value] on each line.

  -d DATA_DIR, --data-dir DATA_DIR
                        Data directory for Base, where the database is
                        stored. Remember that Base must have read/write
                        access. Default is ~/.Base
  -n, --no-text         Do not store what you type. This will make your
                        database smaller and less sensitive to security
                        breaches. Process name, window titles, window
                        geometry, mouse clicks, number of keys pressed and key
                        timings will still be stored, but not the actual
                        letters. Key timings are stored to enable activity
                        calculation in selfstats. If this switch is used,
                        you will never be asked for password.
  -r, --no-repeat       Do not store special characters as repeated
                        characters.
```

Everything you do is stored in a Sqlite database in your DATA_DIR. Each day theyre saved to parquet files which are unilaterally queried along with the sqlite database via duckdb they contain a variety of useful columns, like process names and window titles

Unless you use the --no-text flag, Base will store everything you type in two columns in the database.


### Example Statistics
*"OK, so now all this data will be stored, but what can I use it for?"*

While you can access the Sqlite/duckdb tables directly or, if you like Python, import `models.py` from the Base directory and use those duckdb tables, the standard way to query your data is intended to be via a language model.

Here are some model-agnostic use cases:

*"Damn! The browser just threw away everything I wrote, because I was not logged in."*
"Show me everything I have written the last 30 minutes."

`selfstats --back 30 m --showtext`



*"Hmm.. what is my password for Hoolaboola.com?"*
"show me everything I have ever written in Chrome, where the window title contained something with "Hoolaboola"."

`selfstats -T "Hoolaboola" -P Google-chrome --showtext`



*"I need to remember what I worked on a few days ago, for my time report."*
"What buffers did I have open in Emacs on the tenth of this month and one day forward? Sort by how many keystrokes I wrote in each. This only works if I have set Emacs to display the current buffer in the window title. In general, try to set your programs (editors, terminals, web apps, ...) to include information on what you are doing in the window title. This will make it easier to search for later. On a related but opposite note: if you have the option, remove information like "mails unread" or "unread count" (for example in Gmail and Google Reader) from the window titles, to make it easier to group them in --tactive and --tkeys."


`selfstats --date 10 --limit 1 d -P emacs --tkeys`


*"Also, when and how much have I used my computer this last week?"*
"display my active time periods for the last week. consider it inactive when I have not clicked or used the keyboard in 180 seconds." 

`selfstats -b 1 w --periods 180`


*"How effective have I been this week?"*
"show ratios informing me about how much I have written per active second and how much I have clicked vs used the keyboard. cause = a lot of clicking means too much browsing or inefficient use of my tools."

`selfstats -b 1 w --ratios`



*"I remember that I wrote something to her about the IP address of our printer a few months ago. I can't quite remember if it was a chat, a tweet, a mail, a facebook post, or what.. Should I search them separately? No."*
"Find all texts where I mentioned the word 'printer' in the last 10 weeks"
`selfstats --body printer -s --back 40 w`

*"What programs do I use the most?"*
"List all programs I have ever used, ordered by time spent active in them"
`selfstats --pactive`

*"Which questions on the website Stack Overflow did I visit yesterday?"*  
"Show me all window titles containing 'Stack Overflow' from the last 32 hours, sorted by active time"
`./selfstats -T "Stack Overflow" -P Google-chrome --back 32 h --tactive`

*"How much have I browsed today?"*
"List all the different pages I visited in Chrome today, ordered by active time"
`selfstats -P Google-chrome --clock 00:00 --tactive`

*"Who needs Qwerty? I am going to make an alternative super-programmer-keymap. I wonder what keys I use the most when I code C++?"*
"Show me the most frequently pressed keys in Emacs while editing files with 'cpp' in the name"
`selfstats --key-freq -P Emacs -T cpp`

*"While we are at it, which cpp files have I edited the most this month?"*
"List the cpp files I edited in Emacs this month, sorted by amount typed"
`selfstats -P Emacs -T cpp --tkeys --date 1`
Selfstats is a swiss army knife of self knowledge. Experiment with it when you have acquired a few days of data. Remember that if you know SQL or SqlAlchemy, it is easy to construct your own queries against the database to get exactly the information you want, make pretty graphs, etc. There are a few stored properties, like coordinates of a mouse click and window geometry, that you can currently only reach through the database.

### Selfstats Reference

The --help is a beast that right now looks something like this:

```
usage: selfstats [-h] [-c FILE] [-d DATA_DIR] [-s]
                    [-D DATE [DATE ...]] [-C CLOCK] [-i ID]
                    [-b BACK [BACK ...]] [-l LIMIT [LIMIT ...]] [-m nr]
                    [-T regexp] [-P regexp] [-B regexp] [--ratios] [--clicks]
                    [--key-freqs] [--human-readable] [--active [seconds]] [--periods [seconds]]
                    [--pactive [seconds]] [--tactive [seconds]] [--pkeys]
                    [--tkeys]

Calculate statistics on Base data. Per default it will show non-text
information that matches the filter. Adding '-s' means also show text. Adding
any of the summary options will show those summaries over the given filter
instead of the listing. Multiple summary options can be given to print several
summaries over the same filter. If you give arguments that need to access text
/ keystrokes, you will be asked for the decryption password.

optional arguments:
  -h, --help            show this help message and exit
  -c FILE, --config FILE
                        Config file with defaults. Command line parameters
                        will override those given in the config file. Options
                        to Base goes in the "[Defaults]" section, followed
                        by [argument]=[value] on each line. Options specific
                        to selfstats should be in the "[Selfstats]" section,
                        though "data-dir" is still read from "[Defaults]".
  -d DATA_DIR, --data-dir DATA_DIR
                        Data directory for Base, where the database is
                        stored. Remember that Base must have read/write
                        access. Default is ~/.Base
  -s, --showtext        Also show the text column. This switch is ignored if
                        at least one of the summary options are used. Requires
                        password.
  -D DATE [DATE ...], --date DATE [DATE ...]
                        Which date to start the listing or summarizing from.
                        If only one argument is given (--date 13) it is
                        interpreted as the closest date in the past on that
                        day. If two arguments are given (--date 03 13) it is
                        interpreted as the closest date in the past on that
                        month and that day, in that order. If three arguments
                        are given (--date 2012 03 13) it is interpreted as
                        YYYY MM DD
  -C CLOCK, --clock CLOCK
                        Time to start the listing or summarizing from. Given
                        in 24 hour format as --clock 13:25. If no --date is
                        given, interpret the time as today if that results in
                        sometimes in the past, otherwise as yesterday.
  -i ID, --id ID        Which row ID to start the listing or summarizing from.
                        If --date and/or --clock is given, this option is
                        ignored.
  -b BACK [BACK ...], --back BACK [BACK ...]
                        --back <period> [<unit>] Start the listing or summary
                        this much back in time. Use this as an alternative to
                        --date, --clock and --id. If any of those are given,
                        this option is ignored. <unit> is either "s"
                        (seconds), "m" (minutes), "h" (hours), "d" (days) or
                        "w" (weeks). If no unit is given, it is assumed to be
                        hours.
  -l LIMIT [LIMIT ...], --limit LIMIT [LIMIT ...]
                        --limit <period> [<unit>]. If the start is given in
                        --date/--clock, the limit is a time period given by
                        <unit>. <unit> is either "s" (seconds), "m" (minutes),
                        "h" (hours), "d" (days) or "w" (weeks). If no unit is
                        given, it is assumed to be hours. If the start is
                        given with --id, limit has no unit and means that the
                        maximum row ID is --id + --limit.
  -m nr, --min-keys nr  Only allow entries with at least <nr> keystrokes
  -T regexp, --title regexp
                        Only allow entries where a search for this <regexp> in
                        the window title matches something. All regular expressions
                        are case insensitive.
  -P regexp, --process regexp
                        Only allow entries where a search for this <regexp> in
                        the process matches something.
  -B regexp, --body regexp
                        Only allow entries where a search for this <regexp> in
                        the body matches something. Do not use this filter
                        when summarizing ratios or activity, as it has no
                        effect on mouse clicks. Requires password.
  --clicks              Summarize number of mouse button clicks for all
                        buttons.
  --key-freqs           Summarize a table of absolute and relative number of
                        keystrokes for each used key during the time period.
                        Requires password.
  --human-readable      This modifies the --body entry and honors backspace.
  --active [seconds]    Summarize total time spent active during the period.
                        The optional argument gives how many seconds after
                        each mouse click (including scroll up or down) or
                        keystroke that you are considered active. Default is
                        180.
  --ratios [seconds]    Summarize the ratio between different metrics in the
                        given period. "Clicks" will not include up or down
                        scrolling. The optional argument is the "seconds"
                        cutoff for calculating active use, like --active.
  --periods [seconds]   List active time periods. Optional argument works same
                        as for --active.
  --pactive [seconds]   List processes, sorted by time spent active in them.
                        Optional argument works same as for --active.
  --tactive [seconds]   List window titles, sorted by time spent active in
                        them. Optional argument works same as for --active.
  --pkeys               List processes sorted by number of keystrokes.
  --tkeys               List window titles sorted by number of keystrokes.

```

### Email
To monitor that Base works as it should and to continuously get feedback on yourself, it is good to  regularly mail yourself some statistics. I think the easiest way to automate this is using [sendEmail](http://www.debianadmin.com/how-to-sendemail-from-the-command-line-using-a-gmail-account-and-others.html), which can do neat stuff like send through your Gmail account.

For example, put something like this in your weekly [cron](http://clickmojo.com/code/cron-tutorial.html) jobs:
`/(PATH_TO_FILE)/selfstats --back 1 w --ratios 900 --periods 900 | /usr/bin/sendEmail -q -u "Weekly selfstats" <etc..>`
This will give you some interesting feedback on how much and when you have been active this last week and how much you have written vs moused, etc.

# next steps
1. integrate a model api, and ideally a model trained to make duckdb queries intellgently 
2. integrate a part of speech tagging model to categorize on an additional axis based on key terms
3. develop a ui to chat with the model comfortably and display the activity the user was participating in at any given moment
4. integrate tooling for a local model to manage and schedule a task list based on the context of the current conversation
5. integrate an efficient stt model to transcribe all audio and store it as well
6. integrate an OCR model to capture any text which may get missed, and to parse over the already collected screenshots in current databases that lack the OCR functionality
