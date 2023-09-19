import socket
import threading
import time

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, run_async, Filters, MessageHandler, ConversationHandler, \
    CallbackQueryHandler, CallbackContext

from py3cw.DbManager import DBHelper
from py3cw.BotManager import BotManager
from config import config


QUESTIONS, OPTIONS, SHARE = range(3)

poll_data = {'question': 0, "options": []}
options = []


class TelegramManager(threading.Thread):
    def __init__(self, TG_KEY: str):
        self.TG_KEY = TG_KEY
        self.__last = None
        self.botManager = BotManager()
        self.__last_time = None
        self.isVerify = False
        self.updater = Updater(
            self.TG_KEY, workers=10, use_context=True)
        self.DB = DBHelper()
        pass

    def start_bot(self):
        try:
            dispatcher = self.updater.dispatcher
            dispatcher.add_handler(CommandHandler('start', self.start))

            dispatcher.add_handler(CommandHandler('getBalance', self.getBalance))
            dispatcher.add_handler(CommandHandler('startAnalyze', self.StartAnalyze))
            dispatcher.add_handler(CommandHandler('getSymbols', self.GetCoins))
            dispatcher.add_handler(CommandHandler('getRecomendation', self.GetRecomendation))


            dispatcher.add_handler(MessageHandler(Filters.poll, self.receive_poll))
            dispatcher.add_handler(CallbackQueryHandler(self.button_callback))

            '''conversation_handler = ConversationHandler(
                entry_points=[CommandHandler('startAnalyze', self.StartAnalyze, pass_user_data=True)],
                states={
                    QUESTIONS: [MessageHandler(Filters.text, self.questions, pass_user_data=True)],
                    OPTIONS: [MessageHandler(Filters.text, self.options, pass_user_data=True)],
                },
                fallbacks=[CallbackQueryHandler(self.cancel_poll, pass_user_data=True)],
                conversation_timeout=60,
            )
            dispatcher.add_handler(conversation_handler)'''

            dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.new_user_join))
            # dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, self.left_chat_member))
            # dispatcher.add_handler(CommandHandler("check", self.Startcheckingbalances, pass_job_queue=True))
            #self.start_checking_balances_auto(is_from_set_balance=False)

            self.updater.start_polling()
            self.updater.idle()
        except Exception as e:
            print(e)

    def start(self, update, context):
        type = update.message.chat.type
        user = update.message.from_user
        print(type)
        text = "Hello", update.message.chat.id
        update.message.reply_text(text)
        #self.DB.setup()
        mydict = {"TelegramID": update.message.chat.id, "FullName": "{FIRST_NAME} {LAST_NAME}".format(FIRST_NAME=user['first_name'], LAST_NAME=user['last_name'])}
        self.DB.insert_user(mydict)

    @run_async
    def GetCoins(self, update: Update, _: CallbackContext):
        try:
            update.message.chat.send_message(config["coin_list"])
        except Exception as e:
            print(e)
        '''poll_data = {'question': 0, "options": []}
        chat_id = update.message.chat.id
        type = update.message.chat.type

        update.message.chat.send_message("Type indicator")
        return QUESTIONS'''

    @run_async
    def GetRecomendation(self, update: Update, _: CallbackContext):
        try:
            a =self.botManager.Recommendation()
            update.message.chat.send_message(a)
        except Exception as e:
            print(e)
        '''poll_data = {'question': 0, "options": []}
        chat_id = update.message.chat.id
        type = update.message.chat.type

        update.message.chat.send_message("Type indicator")
        return QUESTIONS'''

    @run_async
    def StartAnalyze(self, update: Update, _: CallbackContext):
        try:
            a = self.botManager.IndicatorResults()
            print(a)
            update.message.chat.send_message(a)
        except Exception as e:
            print(e)
        '''poll_data = {'question': 0, "options": []}
        chat_id = update.message.chat.id
        type = update.message.chat.type

        update.message.chat.send_message("Type indicator")
        return QUESTIONS'''

    @run_async
    def get_poll(self, update, context):
        print(update.message.text)
        message = (update.message.text).split()
        if message[0] == config['bot_name']:
            print("Getting poll")
            print(message[1])

    @run_async
    def receive_poll(self, update: Update, _: CallbackContext):
        """On receiving polls, reply to it by a closed poll copying the received poll"""
        actual_poll = update.effective_message.poll
        # Only need to set the question and options, since all other parameters don't matter for
        # a closed poll
        update.effective_message.reply_poll(
            question=actual_poll.question,
            options=[o.text for o in actual_poll.options],
            # with is_closed true, the poll/quiz is immediately closed
            is_closed=True,
            reply_markup=ReplyKeyboardRemove(),
        )

    @run_async
    def receive_poll_answer(self, update: Update, context: CallbackContext):
        """Summarize a users poll vote"""
        answer = update.poll_answer
        poll_id = answer.poll_id
        print(poll_id)
        try:
            questions = context.bot_data[poll_id]["questions"]
        # this means this poll answer update is from an old poll, we can't do our answering then
        except KeyError:
            return
        selected_options = answer.option_ids
        answer_string = ""
        for question_id in selected_options:
            if question_id != selected_options[-1]:
                answer_string += questions[question_id] + " and "
            else:
                answer_string += questions[question_id]

        print(context.bot_data[poll_id])
        context.bot_data[poll_id]["answers"] += 1
        # Close poll after three participants voted
        if context.bot_data[poll_id]["answers"] == 3:
            context.bot.stop_poll(
                context.bot_data[poll_id]["chat_id"], context.bot_data[poll_id]["message_id"]
            )

    @run_async
    def start_polling(self, update: Update, context: CallbackContext) -> None:
        poll_data = {'question': 0, "options": []}
        chat_id = update.message.chat.id
        type = update.message.chat.type


        update.message.chat.send_message("Type indicator")
        return QUESTIONS


    @run_async
    def questions(self, update: Update, context: CallbackContext) -> None:
        print("Questions")
        print(update.message.text)
        poll_data['question'] = update.message.text
        print(poll_data)
        buttons = [
            [
                InlineKeyboardButton("Cancel",
                                     callback_data="cancel_poll"
                                     )
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.chat.send_message("Type at least 2 options", reply_markup=keyboard)
        return OPTIONS

    @run_async
    def options(self, update: Update, context: CallbackContext) -> None:
        print("options")
        print(update.message.text)

        options.append(update.message.text)

        poll_data['options'] = options
        print(poll_data)
        print(options)

        if len(options) >= 2:
            buttons = [
                [
                    InlineKeyboardButton("Finish Answers",
                                         callback_data="share_poll"
                                         )
                ]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.message.chat.send_message("You can finish typing answers", reply_markup=keyboard)
            return OPTIONS
        else:
            buttons = [
                [
                    InlineKeyboardButton("Cancel",
                                         callback_data="cancel_poll"
                                         )
                ]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.message.chat.send_message("Continue typing answers", reply_markup=keyboard)

    @run_async
    def cancel_poll(self, update, context):
        return ConversationHandler.END

    @run_async
    def button_callback(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        choice = query.data

        # Now u can define what choice ("callback_data") do what like this:
        if choice == "share_poll":
            buttons = [
                [
                    InlineKeyboardButton(config['group_names'][0],
                                         callback_data=config['group_ids'][0]
                                         )
                ]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.callback_query.message.chat.send_message("Share this poll in this group:", reply_markup=keyboard)

        elif choice == "cancel_poll":
            update.callback_query.message.chat.send_message("You've successfully cancelled")
            return ConversationHandler.END

        else:
            print(poll_data)
            message = context.bot.send_poll(
                choice,
                poll_data['question'],
                poll_data['options'],
                is_anonymous=False,
                allows_multiple_answers=False,
            )
            # Save some info about the poll the bot_data for later use in receive_poll_answer
            payload = {
                message.poll.id: {
                    "questions": poll_data['options'],
                    "message_id": message.message_id,
                    "chat_id": update.effective_chat.id,
                    "answers": 0,
                }
            }
            context.bot_data.update(payload)
            return ConversationHandler.END

    def getBalance(self, update, context):
        chat_id = update.message.chat.id
        context.bot.send_message(chat_id, "In development")


    @run_async
    def start_checking_balances_auto(self, is_from_set_balance: bool, chat_id=0):
        print("hey")
        if is_from_set_balance:
            balance = self.db.get_group_balance(chat_id)
            text = "Group wallet balance is {BALANCE}. If you have less than that you will be kicked in 30 seconds".format(
                BALANCE=int(balance))
            try:
                self.updater.bot.send_message(chat_id, text)
            except telegram.error.TimedOut:
                self.updater.bot.send_message(chat_id, text)
            self.updater.job_queue.run_repeating(self.check_for_balances, 30, context=[chat_id])
        else:
            isSetCheckBalance = self.db.get_isSet()
            self.updater.job_queue.run_repeating(self.update_balance, 30, context=chat_id)
            for x in isSetCheckBalance:
                print("Group Chat Id = ", x['ChatID'])
                self.updater.job_queue.run_repeating(self.check_for_balances, 10, context=[x['ChatID']])

    def check_for_balances(self, context):
        chat_id = context.job.context[0]
        start = time.time()
        ids, wallet_addresses = self.db.get_users_wallet_address_from_group_id(chat_id)
        group_balance = self.db.get_group_balance(chat_id)
        for i, wallet_address in enumerate(wallet_addresses):
            print("wallet_address = ", wallet_address)
            if wallet_address != None:
                print(ids[i])
                balance = self.db.get_user_token_balance(wallet_address)
                print("Comparing = ", int(balance) < int(group_balance))
                if int(balance) < int(group_balance):
                    self.kick_user(chat_id, ids[i])
            elif wallet_address == None:
                self.updater.bot.kick_chat_member(chat_id=chat_id, user_id=ids[i])

            print("Balance = ", balance * 10 ** -18)
        end = time.time()
        print('Elapsed Time checkForBalance= ', end - start)

    '''
    #Below code runs after /check command which is deprecated
    @run_async
    def Startcheckingbalances(self,update: Update, context: CallbackContext):

        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        print("Group Chat Id = ", chat_id)

        try:
            chat_member_status = context.bot.get_chat_member(chat_id, user_id).status.capitalize()
        except telegram.error.TimedOut:
            chat_member_status = context.bot.get_chat_member(chat_id, user_id).status.capitalize()
        if chat_member_status == "creator".capitalize() or \
            chat_member_status == "administrator".capitalize():
            ##
            balance = self.db.get_group_balance(chat_id)
            balance = balance
            try:
                context.bot.send_message(chat_id, "Group wallet balance is {BALANCE}. If you have less than that you will be kicked in 30 seconds".format(BALANCE=int(balance)))
            except telegram.error.TimedOut:
                context.bot.send_message(chat_id, "Group wallet balance is {BALANCE}. If you have less than that you will be kicked in 30 seconds".format(BALANCE=int(balance)))

            print("User initiated checking balances = ", chat_member_status)
            context.job_queue.run_repeating(self.checkForBalance, 30, context=[update, context])

    # Below code runs after /check command related to Startcheckingbalances function which is deprecated
    def checkForBalance(self, context):
        update = context.job.context[0]
        _context = context.job.context[1]
        chat_id = update.message.chat.id
        start = time.time()
        icon_service = IconSdkManager()
        ids, wallet_addresses = self.db.get_users_wallet_address_from_group_id(chat_id)
        group_balance = self.db.get_group_balance(chat_id)
        for i, wallet_address in enumerate(wallet_addresses):
            print("wallet_address = ", wallet_address)
            if wallet_address!=None:
                print(ids[i])
                balance = icon_service.getTokenBalance(wallet_address)
                print("Comparing = ", int(balance) < int(group_balance))
                if int(balance) < int(group_balance):
                    try:
                        unix_time = time.time()
                        status, kick_count = self.db.update_user_after_kicked_from_group(chat_id=chat_id, id=ids[i])
                        if kick_count + 1 < 3:
                            try:
                                _context.bot.send_message(chat_id,"Kicked for not having enough balance. Kick count = {KICK_COUNT}".format(KICK_COUNT=kick_count+1))
                                time.sleep(1)
                                _context.bot.kick_chat_member(chat_id=chat_id, user_id=ids[i], until_date=unix_time + 35)
                            except Exception:
                                _context.bot.send_message(chat_id,"Kicked for not having enough balance. Kick count = {KICK_COUNT}".format(KICK_COUNT=kick_count + 1))
                                time.sleep(1)
                                _context.bot.kick_chat_member(chat_id=chat_id, user_id=ids[i], until_date=unix_time + 35)
                        else:
                            try:
                                _context.bot.send_message(chat_id,"Banned for not having enough balance. Kick count = {KICK_COUNT}".format(KICK_COUNT=kick_count+1))
                                time.sleep(1)
                                _context.bot.kick_chat_member(chat_id=chat_id, user_id=ids[i], until_date=0)
                                self.db.delete_user_from_group(chat_id, ids[i])
                            except Exception:
                                _context.bot.send_message(chat_id,"Banned for not having enough balance. Kick count = {KICK_COUNT}".format(KICK_COUNT=kick_count + 1))
                                time.sleep(1)
                                _context.bot.kick_chat_member(chat_id=chat_id, user_id=ids[i], until_date=0)
                                self.db.delete_user_from_group(chat_id, ids[i])

                    except (telegram.error.BadRequest, Exception) as e:
                        print(e)
                        continue
            elif wallet_address==None:
                _context.bot.kick_chat_member(chat_id=chat_id, user_id=ids[i])

            print("Balance = ",balance*10**-18)
        end = time.time()
        print('Elapsed Time checkForBalance= ', end-start)

    '''

    def setBalanceOfGroup(self, update, context):
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        try:
            chat_member_status = context.bot.get_chat_member(chat_id, user_id).status.capitalize()
        except telegram.error.TimedOut:
            chat_member_status = context.bot.get_chat_member(chat_id, user_id).status.capitalize()
        if chat_member_status == "creator".capitalize() or \
                chat_member_status == "administrator".capitalize():
            if len(context.args) != 0:
                self.db.set_group_balance(chat_id, int(context.args[0]))
                text = "Balance has set to {AMOUNT}.".format(AMOUNT=context.args[0])
                try:
                    context.bot.send_message(chat_id, text)
                    self.start_checking_balances_auto(is_from_set_balance=True, chat_id=chat_id)
                except telegram.error.TimedOut:
                    context.bot.send_message(chat_id, text)
                    self.start_checking_balances_auto(is_from_set_balance=True, chat_id=chat_id)

            else:
                text = "Please enter the command properly. /setbalance amount"
                try:
                    context.bot.send_message(chat_id, text)
                except telegram.error.TimedOut:
                    context.bot.send_message(chat_id, text)

    @run_async
    def new_user_join(self, update, context):
        for member in update.message.new_chat_members:
            chat_id = update.message.chat.id
            telegram_id = member.id
            print("New User Group Chat Id = ", chat_id)
            print("Member ID = ", telegram_id)
            if member.id == context.bot.id:
                mydict = {"ChatID": chat_id, "FullName": update.message.chat.title, "Balance": 1,
                          "isSetCheckBalance": False,
                          "Users": [{"ID": 0, "NumberofKicks": 0, "is_kicked": False}]}
                self.db.insert_group(mydict)
                self.start_checking_balances_auto(is_from_set_balance=False)
            else:
                is_already_on_db = self.db.is_already_on_db(chat_id=chat_id, telegram_id=telegram_id)
                '''
                user = self.db.get_user(telegram_id)
                user_balance = self.db.get_user_token_balance(user['wallet_address'])
                group_balance = self.db.get_group_balance(chat_id)

                if int(user_balance) < int(group_balance):
                    self.kick_user(chat_id, telegram_id)
                '''
                if is_already_on_db:
                    can_join = self.db.update_group_user_adding(chat_id=chat_id, telegram_id=telegram_id)
                    if can_join is False:
                        print("is already", member)
                        text = "{USER} you are not verified or you've banned from the group. If you have enough balance please get verified.".format(
                            USER=member.name)
                        try:
                            update.message.reply_text(text)
                        except (socket.timeout, Exception):
                            update.message.reply_text(text)

                        time.sleep(1)
                        context.bot.kick_chat_member(chat_id=chat_id, user_id=telegram_id)
                else:
                    can_join = self.db.insert_user_to_group(chat_id=chat_id, telegram_id=telegram_id)
                    if can_join or member.is_bot:
                        print('New user join')
                    else:
                        print(member)
                        text = "{USER} you are not verified or you've banned from the group. If you have enough balance please get verified.".format(
                            USER=member.name)
                        try:
                            update.message.reply_text(text)
                        except (socket.timeout, Exception):
                            update.message.reply_text(text)
                        time.sleep(1)
                        context.bot.kick_chat_member(chat_id=chat_id, user_id=telegram_id)

    def kick_user(self, chat_id, user_id):
        try:
            unix_time = time.time()
            status, kick_count = self.db.update_user_after_kicked_from_group(chat_id=chat_id, id=user_id)
            if kick_count + 1 < 3:
                kick_text = "Kicked for not having enough balance. Kick count = {KICK_COUNT}".format(
                    KICK_COUNT=kick_count + 1)
                try:
                    self.updater.bot.send_message(chat_id, kick_text)
                    time.sleep(1)
                    self.updater.bot.kick_chat_member(chat_id=chat_id, user_id=user_id,
                                                      until_date=unix_time + 35)
                except Exception:
                    self.updater.bot.send_message(chat_id, kick_text)
                    time.sleep(1)
                    self.updater.bot.kick_chat_member(chat_id=chat_id, user_id=user_id,
                                                      until_date=unix_time + 35)
            else:
                ban_text = "Banned for not having enough balance. Kick count = {KICK_COUNT}".format(
                    KICK_COUNT=kick_count + 1)
                try:
                    self.updater.bot.send_message(chat_id, ban_text)
                    time.sleep(1)
                    self.updater.bot.kick_chat_member(chat_id=chat_id, user_id=user_id, until_date=0)
                    self.db.delete_user_from_group(chat_id, user_id)
                except Exception:
                    self.updater.bot.send_message(chat_id, ban_text)
                    time.sleep(1)
                    self.updater.bot.kick_chat_member(chat_id=chat_id, user_id=user_id, until_date=0)
                    self.db.delete_user_from_group(chat_id, user_id)

        except (telegram.error.BadRequest, Exception) as e:
            print(e)

    '''def left_chat_member(self, update, context):
        update.message.reply_text('Left')'''