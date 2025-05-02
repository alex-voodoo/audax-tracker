# Audax Tracker Telegram Bot

This is a Telegram bot for tracking audax bicycle rides.

Audax is a [non-competitive cycling sport](https://en.wikipedia.org/wiki/Audax_(cycling)) where participants need to complete the route, checking in at controls within certain time constraints.

This bot helps "spectators" to track progress of their favourite participants during an event.  The bot does not maintain its own database of participants and controls, it feeds that data from an external data source, and then sends notifications to the subscribers.

## Setup

### Prerequisites

You need the data source that would provide data by means of an API (see [Remote endpoint protocol](#remote-endpoint-protocol) section below).

This project is tested with Python version 3.11.  Other versions may work too but that is not tested.

You will need administrator privileges if you plan to install the bot as a Linux system service.

### Installation step-by-step

Clone this repository.  Create a virtual Python environment with Python version 3.11 and install `requirements.txt` in that virtual environment.

Follow the [official documentation](https://core.telegram.org/bots#how-do-i-create-a-bot) to register your bot with BotFather.

Configure your instance of the bot.  Follow these steps to complete this process:
1. Open the command terminal and activate the virtual environment that you created above
2. Run `python setup.py` and provide the essential configuration parameters: the API token of your bot, the URL of your data endpoint when requested, and the authentication token that the endpoint would recognise when the bot queries it.  The script will render `src/settings.yaml` that is necessary for the bot to run.
3. Run `python src/bot.py`.  The command should start the bot and run indefinitely.  Find the bot in your Telegram client and talk to it in private.  Initiate the conversation by clicking the Start button in the direct message chat.  The bot will respond with a welcome message, and in the terminal where it is running you will see a log message: _Welcoming user {username} (chat ID {chat_id}), is this the admin?_ where `username` should be your Telegram username.  Copy the chat ID, open `src/settings.yaml` and paste that number as the new value of the `DEVELOPER_CHAT_ID` parameter.
4. Stop the bot by pressing `Ctrl+C` in the terminal, then start it again and send the `/start` command to the bot from your Telegram client.  This time you should see another log message in the terminal where the bot is running: _Welcoming the admin user {username} (chat ID {chat_id})_, and also the bot should show the administrator's menu in response to the `/admin` command.

Now the bot is ready to work.  It can be launched directly by running `python src/bot.py` in a command terminal, or it can be installed as a Linux system service.  The recommended way is first testing the bot in direct mode, tuning the configuration, and then installing it as the system service.  To change the configuration, edit `settings.yaml` (the exact location depends on the mode), then restart the bot.

## Running the bot in direct mode

The bot runs in direct mode if the `AUDAX_TRACKER_SERVICE_MODE` environment variable is not set or not equal to "1".

To launch the bot, activate the Python virtual environment and run `python src/bot.py` in a command terminal.  To stop it gracefully, press `Ctrl+C`.

In direct mode, the bot assumes that its configuration file and persistent state file are located in the same directory where its entry point script is located, which is the `src` subdirectory of this repository.

## Running the bot as a Linux system service

The bot can be registered as a Linux service daemon in a system that runs systemd.  The bot runs in service mode if the `AUDAX_TRACKER_SERVICE_MODE` environment variable is set and is equal to "1", which is provided by the systemd unit configuration.

You will need superuser privileges to proceed.

First configure the bot as explained above, then continue from here.

Run `sudo make install` to install the systemd unit.  The script will copy the bot program files to `/usr/local/lib/audax-tracker`, create the virtual Python environment there, register the systemd unit named `audax-tracker`, and copy `src/settings.yaml` to `/usr/local/etc/audax-tracker/settings.yaml`.  The persistent state **will not** be copied, so at any time you can experiment with direct mode, uninstall or re-install the systemd unit, the persistent state created by the service will not be affected.

In service mode, the bot loads its configuration from `/usr/local/etc/audax-tracker/settings.yaml`, and stores its persistent state in `/var/local/audax-tracker/state.json`.

Start the service by running `sudo sustemctl start audax-tracker`, stop it by running `sudo sustemctl stop audax-tracker`.

## Troubleshooting and error handling

The bot writes log messages to `stdout` and `stderr`.  In service mode these are redirected to `/var/log/audax-tracker.log`.

Should any non-fatal errors occur in the bot, it will send error messages to its administrator user via private Telegram messages.

## Remote endpoint protocol

This section, although not being a strictly defined specification, uses "MAY", "SHOULD", and "MUST" to indicate optional, recommended, and mandatory parts, accordingly, in the spirit of [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

The bot queries data from a remote data source, which MUST be an HTTP server that handles POST requests.  The server MUST provide a single endpoint URL that the bot will send all its requests to.

To prevent unauthorised access to data, the server MAY require the client to provide an authentication token with every request.  This token is an arbitrary combination of characters that SHOULD be known only to the server and to the bot, and SHOULD be difficult to guess (e.g., UUID v4). 

### Request

A request is a JSON dictionary with the following fields:
- `method` is mandatory, it identifies the method to call
- `token` is optional, it authenticates the bot at the server
- other fields may be provided depending on the method

### Response

The server response is a JSON dictionary that has one mandatory field, which is boolean `success` that indicates whether the request was handled with no errors, and the server was able to return the requested data.  If `success` is false, the response will contain error message in the `error_message` field.  Otherwise, it may have additional fields depending on the method.

### Methods

#### get-configuration

Returns the current event configuration.

The method has no parameters.

Returned data:

- `event` is a dictionary with the following fields:
  - `name` is a dictionary where keys are language codes and values are names of the event in that language
  - `start` is the date and time of the start (when the participants are allowed to the distance) in ISO format
  - `finish` is the date and time of the finish (when the finish control closes) in ISO format
- `controls` is a dictionary where keys are control IDs and values are control descriptions.  Each control description is a dictionary that has the following fields:
  - `name` is a dictionary where keys are language codes and values are names of the control in that language
  - `distance` is the distance to the control from the start
  - `finish` is a boolean that indicates whether this control is the finish one
- `participants` is a dictionary where keys are frame plate numbers and values are full names of participants.

Sample response:
```
{
    'success': True,
    'event': {
        'name': {
          'en': 'Chuysky Trakt 2025',
          'ru': 'Чуйский Тракт 2025'
        },
        'start': '2025-07-04T02:00:00+00:00',
        'finish': '2025-07-07T20:14:00+00:00'
    },
    'controls': {
        '1': {
            'name': {
                'en': 'Novosibirsk',
                'ru': 'Новосибирск'
            },
            'distance': 0,
            'finish': False
        },
        '6': {
            'name': {
                'en': 'Toguchin',
                'ru': 'Тогучин'
            },
            'distance': 100,
            'finish': False
        },
        '7': {
            'name': {
                'en': 'Novosibirsk',
                'ru': 'Новосибирск'
            },
            'distance': 200,
            'finish': True
        }
    },
    'participants: {
        '42': 'Joe Blade',
        '281': 'Nancy Smith',
        '112': 'Иван Сидоров'
    }
}
```

#### get-tracking-updates

Returns a list of check-in events.

Parameters:
- `since` (optional) specifies the oldest timestamp for the events to return.  If it is not provided, the server will return all events since the start moment of the event.

Returned data:
- `next_since` is value that the client SHOULD supply as the `since` parameter next time it calls this method.  The client SHOULD NOT parse or modify this value.
- `updates` is a list of dictionaries where each dictionary describes the check-in event with the following fields:
  - `checkin_time` is date and time (in ISO format) when a participant checked in at a control, or None if they quit from the ride there (got DNF status).
  - `frame_plate_number` identifies the participant
  - `control` identifies the control

Sample response:

```
{
    'success': True,
    'next_since': '2025-04-19T19:22:00+00:00',
    'updates': [
        {
            'checkin_time': '2025-04-19T19:21:00Z',
            'frame_plate_number': '66',
            'control': 22
        },
        {
            'checkin_time': None,
            'frame_plate_number': '34',
            'control': 3
        }
    ]
}
```
