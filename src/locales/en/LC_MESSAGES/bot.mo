��    =                    �     �  !   �          ;  3   V     �     �     �     �     �  K     !   ]  ?     I   �  G   	  -   Q       (   �  *   �     �        ,     %   L  "   r     �      �  &   �  &   �          6  &   R  %   y  !   �  '   �  .   �  0   	  ,   I	  .   v	     �	  1   �	  !   �	  +   
  +   @
  1   l
     �
     �
     �
     �
     �
     �
          #     6     I     \     o  '   �  +   �  3   �  9   
  �  D  H   '     p     �     �  %   �     �       #        ?     N  �   e  *   #  L   N  v   �  N     <   a  $   �  A   �               9  H   W  #   �  %   �  /   �  /     h   J  �   �  .   9  +   h  +  �  `   �  #   !  "   E  A   h  E   �  1   �  1   "  I   T     �     �  %   �  :   �      -     N     T     [     d     m     u     z          �     �     �  	   �     �     �  "   �  (   �   BOT_DESCRIPTION BUTTON_ADMIN_RELOAD_CONFIGURATION BUTTON_ADMIN_START_FETCHING BUTTON_ADMIN_STOP_FETCHING CHECKIN_DATE_AND_TIME {month} {day} {hour} {minute} COMMAND_DESCRIPTION_ADD COMMAND_DESCRIPTION_HELP COMMAND_DESCRIPTION_REMOVE COMMAND_DESCRIPTION_STATUS CONTROL_LABEL {name} {distance} ERROR_REPORT_BODY {error_uuid} {traceback} {update} {chat_data} {user_data} ERROR_REPORT_CAPTION {error_uuid} LAST_KNOWN_STATUS_ABANDONED {participant_label} {control_label} LAST_KNOWN_STATUS_FINISH {participant_label} {checkin_time} {result_time} LAST_KNOWN_STATUS_OK {participant_label} {checkin_time} {control_label} LAST_KNOWN_STATUS_UNKNOWN {participant_label} MESSAGE_ABORT MESSAGE_ADMIN_CONFIGURATION_RELOAD_ERROR MESSAGE_ADMIN_CONFIGURATION_RELOAD_SUCCESS MESSAGE_ADMIN_FETCHING_STARTED MESSAGE_ADMIN_FETCHING_STOPPED MESSAGE_ADMIN_FETCHING_STOPPED_AFTER_FAILURE MESSAGE_ADMIN_RELOADING_CONFIGURATION MESSAGE_ADMIN_START_STATUS_UNKNOWN MESSAGE_ALREADY_SUBSCRIBED MESSAGE_CHECKIN_UPDATE {entries} MESSAGE_DM_INTERNAL_ERROR {error_uuid} MESSAGE_MAX_SUBSCRIPTION_COUNT_REACHED MESSAGE_NOT_SUBSCRIBED MESSAGE_NO_SUCH_PARTICIPANT MESSAGE_START {max_subscription_count} MESSAGE_START_PARTICIPANTS_LIST {url} MESSAGE_STATUS_SUBSCRIPTION_EMPTY MESSAGE_STATUS_SUBSCRIPTION_LIST_HEADER MESSAGE_SUBSCRIPTION_ADDED {participant_label} MESSAGE_SUBSCRIPTION_REMOVED {participant_label} MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_SUBSCRIBE MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_UNSUBSCRIBE MESSAGE_UNRECOGNISED_INPUT PIECE_ADMIN_START_STATUS_BEFORE_START {remainder} PIECE_ADMIN_START_STATUS_FINISHED PIECE_ADMIN_START_STATUS_IN_AIR {remainder} PIECE_ADMIN_STATS {controls} {participants} PIECE_CONTROLS_S {count} PIECE_CONTROLS_P {count} PIECE_DATETIME_APR PIECE_DATETIME_AUG PIECE_DATETIME_DEC PIECE_DATETIME_FEB PIECE_DATETIME_JAN PIECE_DATETIME_JUL PIECE_DATETIME_JUN PIECE_DATETIME_MAR PIECE_DATETIME_MAY PIECE_DATETIME_NOV PIECE_DATETIME_OCT PIECE_DATETIME_SEP PIECE_DAYS_S {days} PIECE_DAYS_P {days} PIECE_HOURS_S {hours} PIECE_HOURS_P {hours} PIECE_MINUTES_S {minutes} PIECE_MINUTES_P {minutes} PIECE_PARTICIPANTS_S {count} PIECE_PARTICIPANTS_P {count} Project-Id-Version: PROJECT VERSION
Report-Msgid-Bugs-To: Alexander Dunaev <alexander.dunaev@gmail.com>
POT-Creation-Date: 2025-06-29 23:06+0200
PO-Revision-Date: 2025-03-06 12:37+0100
Last-Translator: Alexander Dunaev <alexander.dunaev@gmail.com>
Language: en
Language-Team: Alexander Dunaev <alexander.dunaev@gmail.com>
Plural-Forms: nplurals=2; plural=(n != 1);
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.17.0
 I will let you know when participants of your choice arrive at controls. Update event information Start sending notifications Stop sending notifications {month} {day} {hour:02d}:{minute:02d} add a participant to your list explain what I can do remove a participant from your list show your list {name} ({distance} km) Error UUID {error_uuid}

Exception traceback:
--------------------

{traceback}

Other data:
-----------

update = {update}

context.chat_data = {chat_data}

context.user_data = {user_data} Report for error <code>{error_uuid}</code> ❌<strong>{participant_label}</strong>
        Abandoned at {control_label} 🏆<strong>{participant_label}</strong>
        Finished {checkin_time}!  Result time: <strong>{result_time}</strong> ✅<strong>{participant_label}</strong>
        {control_label} {checkin_time} ❔<strong>{participant_label}</strong>
        No check-ins Cancelled.  Please select a command. An error occurred while loading data.  See logs for more details. Event data is updated Started sending notifications Stopped sending notifications An error occurred when fetching updates.  Stopped sending notifications. Reloading controls and participants No event is configured at the moment. You have this participant in your list already. News about participants in your list:
{entries} An internal error <code>{error_uuid}</code> occurred.  The administrator is notified about this problem. Your list has reached the maximum allowed number of entries.  To add another participant, unsubscribe from one of your existing ones. You do not have this participant in your list. No participant registered with such number. I will let you know when participants of your choice arrive at controls.

You can have up to {max_subscription_count} in your list.  Use these commands to manage the list:

/add - add a participant to track
/remove - stop tracking a participant
/status - show status of all participants in your list Participants' frame plate numbers are published at the <a href='{url}'>website of the event</a>. Your list of participants is empty. Here is your list of participants: <strong>{participant_label}</strong> has been added to your list. <strong>{participant_label}</strong> has been removed from your list. Please enter frame plate number of a participant. Please enter frame plate number of a participant. I do not know what to answer.  Please use commands available in the menu. Will start in {remainder}. The event is over. In progress, will end in {remainder}. {controls} and {participants} are registered in the system {count} control {count} controls April August December February January July June March May November October September {days} day {days} days {hours} hour {hours} hours {minutes} minute {minutes} minutes {count} participant {count} participants 