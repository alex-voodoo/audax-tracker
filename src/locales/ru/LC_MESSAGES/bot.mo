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
  ,  D  f   q  ?   �  #     %   <  %   b  :   �  3   �  @   �  $   8     ]  �   v  6   Y  S   �  �   �  T   m  F   �  2   	  �   <  9   �  !     '   2  j   Z  >   �  5     Y   :  R   �  �   �  �   v  R   h  R   �      �     2   �  N   �  M   -  R   {  >   �  >     �   L     �  (   �  >   '  O   f  �   �     <     I     X     g     v     �     �  
   �     �     �     �     �  -   �  2     B   5  P   x   BOT_DESCRIPTION BUTTON_ADMIN_RELOAD_CONFIGURATION BUTTON_ADMIN_START_FETCHING BUTTON_ADMIN_STOP_FETCHING CHECKIN_DATE_AND_TIME {month} {day} {hour} {minute} COMMAND_DESCRIPTION_ADD COMMAND_DESCRIPTION_HELP COMMAND_DESCRIPTION_REMOVE COMMAND_DESCRIPTION_STATUS CONTROL_LABEL {name} {distance} ERROR_REPORT_BODY {error_uuid} {traceback} {update} {chat_data} {user_data} ERROR_REPORT_CAPTION {error_uuid} LAST_KNOWN_STATUS_ABANDONED {participant_label} {control_label} LAST_KNOWN_STATUS_FINISH {participant_label} {checkin_time} {result_time} LAST_KNOWN_STATUS_OK {participant_label} {checkin_time} {control_label} LAST_KNOWN_STATUS_UNKNOWN {participant_label} MESSAGE_ABORT MESSAGE_ADMIN_CONFIGURATION_RELOAD_ERROR MESSAGE_ADMIN_CONFIGURATION_RELOAD_SUCCESS MESSAGE_ADMIN_FETCHING_STARTED MESSAGE_ADMIN_FETCHING_STOPPED MESSAGE_ADMIN_FETCHING_STOPPED_AFTER_FAILURE MESSAGE_ADMIN_RELOADING_CONFIGURATION MESSAGE_ADMIN_START_STATUS_UNKNOWN MESSAGE_ALREADY_SUBSCRIBED MESSAGE_CHECKIN_UPDATE {entries} MESSAGE_DM_INTERNAL_ERROR {error_uuid} MESSAGE_MAX_SUBSCRIPTION_COUNT_REACHED MESSAGE_NOT_SUBSCRIBED MESSAGE_NO_SUCH_PARTICIPANT MESSAGE_START {max_subscription_count} MESSAGE_START_PARTICIPANTS_LIST {url} MESSAGE_STATUS_SUBSCRIPTION_EMPTY MESSAGE_STATUS_SUBSCRIPTION_LIST_HEADER MESSAGE_SUBSCRIPTION_ADDED {participant_label} MESSAGE_SUBSCRIPTION_REMOVED {participant_label} MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_SUBSCRIBE MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_UNSUBSCRIBE MESSAGE_UNRECOGNISED_INPUT PIECE_ADMIN_START_STATUS_BEFORE_START {remainder} PIECE_ADMIN_START_STATUS_FINISHED PIECE_ADMIN_START_STATUS_IN_AIR {remainder} PIECE_ADMIN_STATS {controls} {participants} PIECE_CONTROLS_S {count} PIECE_CONTROLS_P {count} PIECE_DATETIME_APR PIECE_DATETIME_AUG PIECE_DATETIME_DEC PIECE_DATETIME_FEB PIECE_DATETIME_JAN PIECE_DATETIME_JUL PIECE_DATETIME_JUN PIECE_DATETIME_MAR PIECE_DATETIME_MAY PIECE_DATETIME_NOV PIECE_DATETIME_OCT PIECE_DATETIME_SEP PIECE_DAYS_S {days} PIECE_DAYS_P {days} PIECE_HOURS_S {hours} PIECE_HOURS_P {hours} PIECE_MINUTES_S {minutes} PIECE_MINUTES_P {minutes} PIECE_PARTICIPANTS_S {count} PIECE_PARTICIPANTS_P {count} Project-Id-Version: PROJECT VERSION
Report-Msgid-Bugs-To: Alexander Dunaev <alexander.dunaev@gmail.com>
POT-Creation-Date: 2025-06-29 23:06+0200
PO-Revision-Date: 2025-03-06 12:37+0100
Last-Translator: Alexander Dunaev <alexander.dunaev@gmail.com>
Language: ru
Language-Team: Alexander Dunaev <alexander.dunaev@gmail.com>
Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.17.0
 Я сообщу, когда выбранные вами участники прибудут на КП. Обновить информацию о мероприятии Запустить рассылку Остановить рассылку {day} {month} {hour:02d}:{minute:02d} добавить участника в ваш список объяснить, что я могу делать удалить участника из вашего списка показать ваш список {name} ({distance} км) UUID ошибки {error_uuid}

Трассировка стека:
------------------

{traceback}

Другие данные:
--------------

update = {update}

context.chat_data = {chat_data}

context.user_data = {user_data} Отчёт об ошибке <code>{error_uuid}</code> ❌ <strong>{participant_label}</strong>
        Сход на КП {control_label} 🏆 <strong>{participant_label}</strong>
        Финиш {checkin_time}! Итоговое время: <strong>{result_time}</strong> ✅ <strong>{participant_label}</strong>
        КП {control_label} {checkin_time} ❔ <strong>{participant_label}</strong>
        Нет отметок Отменено. Выберите команду. Во время загрузки данных произошла ошибка. Больше информации вы найдёте в журналах. Данные о мероприятии обновлены Рассылка запущена Рассылка остановлена При запросе данных возникла ошибка. Рассылка остановлена. Запрашиваю списки КП и участников Нет информации о мероприятии Участник с таким номером уже есть в вашем списке. Новости об участниках из вашего списка:
{entries} Возникла внутренняя ошибка <code>{error_uuid}</code>. Администратор оповещён о проблеме. В вашем списке уже максимально возможное число участников. Чтобы добавить нового участника, удалите одну из существующих подписок. Участника с таким номером нет в вашем списке. Участник с таким номером не зарегистрирован. Я сообщу, когда выбранные вами участники прибудут на КП.

В вашем списке может быть до {max_subscription_count} участников. Для управления списком воспользуйтесь следующими командами:

/add - добавить участника в список
/remove - убрать участника из списка
/status - показать статус всех участников из списка Стартовые номера участников опубликованы на <a href='{url}'>веб-сайте мероприятия</a>. Ваш список участников пуст. В вашем списке сейчас следующие участники: <strong>{participant_label}</strong> теперь в вашем списке. <strong>{participant_label}</strong> больше не в вашем списке. Введите нарамный номер участника: Введите нарамный номер участника: Я не знаю, что ответить. Пожалуйста, воспользуйтесь командами, доступными в меню. До старта {remainder} Мероприятие окончено. Мероприятие идёт, до финиша {remainder} В системе зарегистрированы {controls} и {participants} {count} контрольный пункт {count} контрольного пункта {count} контрольных пунктов апреля августа декабря февраля января июля июня марта мая ноября октября сентября {days} день {days} дня {days} дней {hours} час {hours} часа {hours} часов {minutes} минута {minutes} минуты {minutes} минут {count} участник {count} участника {count} участников 