from three_commas import api, streams
from config import config


class ThreeCommasManager:
    def __init__(self):
        self.apiKey = config['three_commas_api_key']
        self.secretKey = config['three_commas_secret_key']

    def deneme(self):
        x = api.ver1.bots.get(api_key=self.apiKey, api_secret=self.secretKey)
        print(x)
    def get_order(self):
        error, bot = api.ver1.bots.get_show_by_id()
        # base_order_volume is a float
        base_order_volume = bot.get_base_order_volume()
    @streams.deals(api_key = config['three_commas_api_key'], api_secret= config['three_commas_secret_key'])
    def handle_deals(self, deal: streams.streams.DealEntity):
        # do your awesome stuff with the deal
        print(deal)  # {'id': 1311811868, 'type': 'Deal', 'bot_id': 6313165, 'max_safety_orders': 6, 'deal_has_error': False ....
        print(deal.account_id)  # 99648312
        print(deal.created_at)  # string object '2022-02-18T05:26:06.803Z'
        print(deal.parsed(True).created_at)  # datetime.datetime object
        print(deal.bought_amount)

if __name__ == '__main__':
    three_commas = ThreeCommasManager()
    three_commas.deneme()