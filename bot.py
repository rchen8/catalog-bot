from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
import json
import locale
import os
import re
import redis
import requests
import traceback
import tweepy

def send_discord_notification(content):
  url = 'https://discordapp.com/api/webhooks/%s/%s' % \
      (os.environ['DISCORD_ID'], os.environ['DISCORD_TOKEN'])
  requests.post(url, data={'content': content})

def get_eth_price():
  try:
    return CoinGeckoAPI().get_price(ids='ethereum', vs_currencies='usd')['ethereum']['usd']
  except:
    url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms=ETH&tsyms=USD'
    return requests.get(url).json()['ETH']['USD']

### CATALOG ########################################################################################

catalog_ids = [10210, 10209, 10208, 10207, 10206, 10203, 10196, 10195, 10193, 10190, 10163, 10118, 10035, 10034, 10031, 10022, 10008, 10007, 10005, 10004, 10003, 10002, 9992, 9990, 9989, 9984, 9981, 9980, 9979, 9976, 9974, 9973, 9972, 9971, 9969, 9968, 9967, 9966, 9965, 9933, 9929, 9926, 9925, 9924, 9756, 9739, 9735, 9712, 9711, 9707, 9703, 9696, 9693, 9692, 9691, 9689, 9688, 9681, 9676, 9673, 9662, 9660, 9659, 9658, 9657, 9656, 9654, 9652, 9641, 9640, 9639, 9633, 9632, 9630, 9626, 9624, 9620, 9614, 9611, 9610, 9607, 9599, 9588, 9572, 9571, 9567, 9550, 9549, 9548, 9547, 9545, 9544, 9541, 9538, 9537, 9517, 9510, 9505, 9501, 9500, 9487, 9499, 9496, 9449, 9420, 9418, 9416, 9413, 9412, 9411, 9410, 9409, 9408, 9406, 9405, 9404, 9373, 9372, 9363, 9357, 9353, 9350, 9349, 9348, 9346, 9313, 9140, 9105, 9097, 9032, 9028, 9010, 9007, 9004, 8931, 8930, 8929, 8927, 8925, 8921, 8915, 8914, 8912, 8911, 8910, 8909, 8908, 8907, 8888, 8886, 8885, 8884, 8880, 8879, 8876, 8871, 8870, 8869, 8868, 8865, 8864, 8863, 8861, 8853, 8852, 8847, 8846, 8845, 8844, 8843, 8841, 8822, 8818, 8815, 8812, 8808, 8807, 8803, 8802, 8801, 8799, 8793, 8791, 8790, 8789, 8788, 8781, 8778, 8777, 8774, 8773, 8771, 8760, 8759, 8758, 8757, 8755, 8753, 8751, 8701, 8699, 8697, 8696, 8683, 8682, 8679, 8665, 8663, 8660, 8652, 8650, 8649, 8648, 8616, 8584, 8582, 8580, 8579, 8571, 8570, 8569, 8568, 8565, 8564, 8563, 8558, 8557, 8555, 8541, 8532, 8528, 8527, 8520, 8519, 8518, 8505, 8504, 8494, 8474, 8468, 8467, 8461, 8460, 8446, 8445, 8444, 8442, 8432, 8431, 8422, 8417, 8415, 8414, 8413, 8398, 8395, 8388, 8387, 8385, 8381, 8376, 8375, 8374, 8364, 8359, 8352, 8342, 8334, 8333, 8329, 8328, 8323, 8319, 8295, 8285, 8282, 8272, 8264, 8261, 8260, 8258, 8254, 8249, 8246, 8245, 8244, 8243, 8242, 8241, 8240, 8239, 8238, 8237, 8236, 8235, 8234, 8232, 8231, 8230, 8228, 8221, 8216, 8213, 8211, 8206, 8195, 8193, 8192, 8191, 8190, 8186, 8185, 8184, 8181, 8179, 8156, 8155, 8154, 8153, 8151, 8150, 8149, 8148, 8145, 8141, 8138, 8136, 8135, 8134, 8131, 8130, 8123, 8122, 8117, 8115, 8107, 8103, 8102, 8100, 8099, 8091, 8078, 8073, 8069, 8068, 8067, 8066, 8065, 8063, 8062, 8050, 8046, 8038, 7986, 7984, 7980, 7979, 7976, 7959, 7957, 7907, 7906, 7905, 7902, 7900, 7898, 7897, 7896, 7893, 7892, 7889, 7888, 7887, 7886, 7883, 7882, 7880, 7879, 7878, 7875, 7874, 7869, 7852, 7849, 7848, 7832, 7831, 7827, 7825, 7824, 7821, 7820, 7815, 7809, 7808, 7807, 7806, 7804, 7802, 7801, 7794, 7791, 7790, 7788, 7783, 7780, 7778, 7777, 7776, 7775, 7774, 7770, 7767, 7766, 7761, 7758, 7750, 7746, 7744, 7738, 7735, 7723, 7719, 7718, 7717, 7714, 7708, 7706, 7704, 7702, 7703, 7701, 7699, 7698, 7697, 7688, 7687, 7686, 7684, 7679, 7678, 7677, 7663, 7661, 7660, 7658, 7656, 7655, 7652, 7650, 7641, 7638, 7632, 7630, 7610, 7601, 7596, 7586, 7585, 7584, 7578, 7579, 7572, 7571, 7569, 7562, 7559, 7553, 7546, 7540, 7526, 7523, 7519, 7517, 7516, 7515, 7507, 7506, 7504, 7503, 7499, 7492, 7489, 7481, 7478, 7477, 7476, 7475, 7465, 7456, 7454, 7446, 7443, 7431, 7429, 7427, 7425, 7419, 7417, 7407, 7408, 7404, 7402, 7395, 7392, 7391, 7386, 7384, 7374, 7371, 7365, 7360, 7357, 7355, 7353, 7340, 7339, 7338, 7337, 7336, 7335, 7334, 7333, 7331, 7329, 7328, 7327, 7326, 7323, 7322, 7319, 7315, 7314, 7310, 7305, 7302, 7301, 7297, 7293, 7290, 7285, 7284, 7282, 7280, 7276, 7275, 7274, 7273, 7272, 7270, 7268, 7266, 7262, 7261, 7251, 7244, 7243, 7242, 7230, 7228, 7224, 7222, 7214, 7213, 7208, 7206, 7205, 7204, 7203, 7199, 7197, 7195, 7191, 7187, 7186, 7185, 7169, 7163, 7162, 7119, 7118, 7113, 7112, 7111, 7052, 7032, 7031, 7024, 7021, 7012, 7010, 6958, 6956, 6955, 6954, 6952, 6939, 6923, 6909, 6906, 6905, 6904, 6855, 6835, 6834, 6833, 6791, 6780, 6769, 6768, 6748, 6747, 6744, 6737, 6735, 6731, 6723, 6722, 6719, 6717, 6716, 6708, 6704, 6701, 6700, 6699, 6698, 6693, 6675, 6673, 6657, 6656, 6651, 6646, 6638, 6621, 6614, 6608, 6590, 6589, 6586, 6584, 6581, 6580, 6577, 6559, 6555, 6554, 6553, 6540, 6534, 6533, 6519, 6518, 6517, 6516, 6505, 6494, 6473, 6470, 6463, 6462, 6461, 6460, 6459, 6458, 6454, 6449, 6444, 6437, 6436, 6433, 6431, 6407, 6416, 6411, 6388, 6387, 6382, 6380, 6375, 6360, 6358, 6356, 6353, 6348, 6347, 6345, 6344, 6343, 6333, 6329, 6328, 6325, 6324, 6321, 6320, 6314, 6313, 6310, 6311, 6308, 6305, 6304, 6303, 6302, 6301, 6300, 6299, 6298, 6291, 6287, 6276, 6275, 6274, 6273, 6265, 6257, 6249, 6246, 6244, 6236, 6235, 6233, 6230, 6227, 6224, 6223, 6221, 6220, 6219, 6216, 6214, 6213, 6211, 6209, 6208, 6205, 6204, 6203, 6202, 6200, 6199, 6198, 6193, 6192, 6187, 6260, 6184, 6183, 6181, 6180, 6179, 6176, 6175, 6171, 6164, 6161, 6158, 6148, 6147, 6145, 6141, 6140, 6138, 6133, 6127, 6126, 6124, 6117, 6115, 6108, 6107, 6106, 6104, 6103, 6098, 6092, 6089, 6088, 6087, 6085, 6116, 6083, 6082, 6112, 6073, 6072, 6071, 6070, 6065, 6064, 6063, 6060, 6057, 6059, 6056, 6048, 6047, 6041, 6037, 6036, 6035, 6034, 6033, 6032, 6031, 6030, 6029, 6028, 6027, 6025, 6024, 6021, 6020, 6022, 6019, 6018, 6016, 6014, 6012, 6011, 6008, 6005, 6004, 6002, 6001, 6000, 5999, 5997, 5994, 5992, 5991, 5986, 5990, 5989, 5988, 5987, 5984, 5979, 5978, 5967, 5955, 5951, 5949, 5945, 5944, 5943, 5942, 5937, 5936, 5929, 5916, 5915, 5912, 5911, 5910, 5909, 5908, 5907, 5906, 5905, 5904, 5903, 5900, 5899, 5882, 5896, 5885, 5883, 5881, 5880, 5867, 5858, 5857, 5855, 5851, 5836, 5833, 5829, 5828, 5825, 5822, 5819, 5818, 5817, 5811, 5808, 5753, 5796, 5792, 5791, 5789, 5787, 5786, 5785, 5782, 5781, 5772, 5770, 5768, 5752, 5748, 5746, 5734, 5733, 5726, 5714, 5694, 5704, 5691, 5685, 5684, 5682, 5681, 5679, 5676, 5665, 5664, 5663, 5662, 5661, 5659, 5658, 5656, 5653, 5645, 5644, 5643, 5642, 5641, 5640, 5639, 5631, 5632, 5629, 5630, 5628, 5627, 5626, 5615, 5614, 5613, 5612, 5611, 5610, 5609, 5594, 5593, 5591, 5560, 5559, 5557, 5556, 5552, 5543, 5541, 5540, 5538, 5533, 5532, 5530, 5522, 5521, 5520, 5517, 5516, 5515, 5514, 5511, 5510, 5509, 5508, 5507, 5506, 5505, 5504, 5503, 5502, 5500, 5499, 5498, 5497, 5495, 5494, 5493, 5492, 5491, 5490, 5489, 5487, 5486, 5485, 5481, 5477, 5474, 5468, 5467, 5462, 5461, 5460, 5459, 5344, 5343, 5331, 5296, 4959, 4955, 4954, 4953, 4933, 4932, 4931, 4916, 4902, 4900, 4891, 4885, 4883, 4857, 4856, 4841, 4832, 4819, 4818, 4817, 4808, 4807, 4801, 4793, 4785, 4762, 4751, 4749, 4747, 4741, 4729, 4727, 4710, 4699, 4681, 4674, 4600, 4591, 4559, 4547, 4546, 4510, 4491, 4373, 4371, 4367, 4345, 4344, 4318, 4285, 4281, 4278, 4267, 4262, 4255, 4245, 4227, 4224, 4222, 4221, 4213, 4212, 4210, 4203, 4198, 4169, 4162, 4139, 4107, 4106, 4105, 4079, 4078, 4064, 4033, 3964, 3962, 3961, 3925, 3889, 3880, 3785, 3774, 3771, 3766, 3763, 3756, 3752, 3746, 3743, 3739, 3737, 3735, 3734, 3733, 3732, 3731, 3730, 3729, 3728, 3727, 3726, 3543, 3523, 3516, 3468, 3455, 3412, 3398, 3397, 3382, 3375, 3344, 3319, 3310, 3183, 3169, 3168, 3167, 3166, 3157, 3131, 3121, 3116, 3115, 3104, 3092, 3085, 3078, 3076, 3056, 3035, 3030, 3029, 3028, 2969, 2958, 2957, 2955, 2953, 2912, 2880, 2872, 2867, 2817, 2773, 2762, 2685, 2632, 2631, 2630, 2628, 2627, 2625, 2623, 2620, 2619, 2616, 2615, 2613, 2611, 2610, 2608, 2604, 2603, 2601, 2598, 2597, 2595, 2585, 2561, 2543, 2471, 2422, 2258, 2247, 2200, 2183, 2182, 2177, 2165, 2156, 2114, 2107, 2083, 2047, 2010, 2004, 1974, 1971, 1966, 1967, 1931, 1835, 1753, 1750, 1738, 1731, 1729, 1727, 1725, 1724, 1722, 1719, 1717, 1715, 1712, 1711, 1710, 1709, 1708, 1706, 1700, 1678]
catalog_contract = '0x0bC2A24ce568DAd89691116d5B34DEB6C203F342'

def get_catalog_record(id, contract_address):
  url = 'https://indexer-prod-mainnet.hasura.app/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'GetTokenById',
    'query': """
      query GetTokenById($tokenId: String!, $tokenContractAddress: String!) {
        Token(
          where: {_and: {address: {_eq: $tokenContractAddress}, tokenId: {_eq: $tokenId}}}
        ) {
          ...IndexerTokenFragment
        }
      }
      fragment IndexerTokenFragment on Token {
        auctions(order_by: {createdEvent: {blockNumber: desc}}) {
          ...IndexerAuctionFragment
        }
        media {
          ...IndexerMediaFragment
        }
        minter
        owner
        v3Events(order_by: {blockNumber: desc_nulls_last}) {
          ...V3Event
        }
      }
      fragment IndexerAuctionFragment on Auction {
        currency {
          decimals
          symbol
        }
        lastBidAmount
        lastBidder
      }
      fragment IndexerMediaFragment on Media {
        askEvents(order_by: {blockNumber: desc}) {
          ...AskEventFragment
        }
      }
      fragment AskEventFragment on MarketAskEvent {
        amount
        currency
      }
      fragment V3Event on Event {
        details
        eventType
      }""",
    'variables': {'tokenId': str(id), 'tokenContractAddress': contract_address}
  }
  return requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['Token'][0]

def get_catalog_records():
  url = 'https://catalog-prod.hasura.app/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'GetTracks',
    'query': """
      query GetTracks {
        tracks(order_by: {created_at: desc}) {
          ...TrackFragment
          __typename
        }
      }
      fragment TrackFragment on tracks {
        artist {
          handle
          id
          name
        }
        contract_address
        nft_id
        short_url
        title
        __typename
      }""",
    'variables': None
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()['data']['tracks']
  return {(int(track['nft_id']), track['contract_address']):
      track for track in response if track['nft_id'] is not None}

def get_username(address):
  url = 'https://catalog-prod.hasura.app/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'GetUsersFromAddresses',
    'query': """
      query GetUsersFromAddresses {
        catalog_users(where: {id: {_eq: "%s"}}) {
          handle
          id
          name
          links {
            type
            url
          }
        }
      }""" % address.lower(),
    'variables': None
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['catalog_users']

  if len(response) == 0:
    return address[0:6].lower()
  for link in response[0]['links']:
    if link['type'] == 'TWITTER':
      handle = link['url']
      replacement = ['http://', 'https://', 'www.', 'twitter.com/']
      for text in replacement:
        handle = re.compile(re.escape(text), re.IGNORECASE).sub('', handle)
      return '@' + handle.replace('/', '')
  return response[0]['name']

### ZORA ###########################################################################################

zora_contract = '0xabEFBc9fD2F806065b4f3C237d4b59D9A97Bcac7'

def get_zora_bid_events(last_block_number):
  url = 'https://indexer-prod-mainnet.zora.co/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'Catalog',
    'query': """
      query Catalog {
        AuctionBidEvent(where: {
          firstBid: {_eq: true},
          blockNumber: {_gte: %s},
          tokenContract: {_in: ["0x0bC2A24ce568DAd89691116d5B34DEB6C203F342", "0xabEFBc9fD2F806065b4f3C237d4b59D9A97Bcac7"]}
        }) {
          blockNumber
          tokenContract
          tokenId
        }
      }""" % last_block_number,
    'variables': None
  }

  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['AuctionBidEvent']
  if len(response) > 0:
    r.set('last_block_number', max(int(r.get('last_block_number')),
        max([bid['blockNumber'] for bid in response])))

  auctions = []
  for bid in response:
    if bid['tokenContract'] == catalog_contract or int(bid['tokenId']) in catalog_ids:
      auctions.append((int(bid['tokenId']), bid['tokenContract']))
  return auctions

def get_zora_auction_events(last_block_number):
  address = '0xe468ce99444174bd3bbbed09209577d25d1ad673'
  topic0 = '0x4f35fb3ea0081b3ccbe8df613cab0f9e1694d50a025e0aa09b88a86a3d07c2de'
  url = 'https://api.etherscan.io/api?' + \
      'module=logs&action=getLogs&fromBlock=%s&toBlock=latest&address=%s&topic0=%s&apikey=%s' % \
      (last_block_number, address, topic0, os.environ['ETHERSCAN_API_KEY'])

  sales = []
  for event in requests.get(url).json()['result']:
    token_id = int(event['topics'][2], 16)
    contract_address = '0x' + event['topics'][3][-40:]
    if contract_address == zora_contract.lower() and token_id in catalog_ids:
      sales.append((token_id, zora_contract, 'auction'))
    elif contract_address == catalog_contract.lower():
      sales.append((token_id, catalog_contract, 'auction'))
    r.set('last_block_number', max(int(r.get('last_block_number')), int(event['blockNumber'], 16)))
  return sales

def get_zora_market_events(last_block_number):
  address = '0xe5bfab544eca83849c53464f85b7164375bdaac1'
  topic0 = '0xb6ef177c7a6f32b283a49b5e0463a39240cdaa278028dfb219480d050e8ee54c'
  url = 'https://api.etherscan.io/api?' + \
      'module=logs&action=getLogs&fromBlock=%s&toBlock=latest&address=%s&topic0=%s&apikey=%s' % \
      (last_block_number, address, topic0, os.environ['ETHERSCAN_API_KEY'])

  sales = []
  for event in requests.get(url).json()['result']:
    token_id = int(event['topics'][1], 16)
    if token_id in catalog_ids:
      sales.append((token_id, zora_contract, 'market'))
    r.set('last_block_number', max(int(r.get('last_block_number')), int(event['blockNumber'], 16)))
  return sales

def get_zora_v3_asks_events(last_block_number):
  address = '0x6170b3c3a54c3d8c854934cbc314ed479b2b29a3'
  topic0 = '0x21a9d8e221211780696258a05c6225b1a24f428e2fd4d51708f1ab2be4224d39'
  url = 'https://api.etherscan.io/api?' + \
      'module=logs&action=getLogs&fromBlock=%s&toBlock=latest&address=%s&topic0=%s&apikey=%s' % \
      (last_block_number, address, topic0, os.environ['ETHERSCAN_API_KEY'])

  sales = []
  for event in requests.get(url).json()['result']:
    token_id = int(event['topics'][2], 16)
    contract_address = '0x' + event['topics'][1][-40:]
    if contract_address == zora_contract.lower() and token_id in catalog_ids:
      sales.append((token_id, zora_contract, 'asks'))
    elif contract_address == catalog_contract.lower():
      sales.append((token_id, catalog_contract, 'asks'))
    r.set('last_block_number', max(int(r.get('last_block_number')), int(event['blockNumber'], 16)))
  return sales

def get_zora_sales(last_block_number):
  sales = get_zora_auction_events(last_block_number)
  for sale in get_zora_market_events(last_block_number):
    if sale[0] not in [x[0] for x in sales]:
      sales.append(sale)
  return sales + get_zora_v3_asks_events(last_block_number)

def get_currency(contract_address):
  url = 'https://indexer-prod-mainnet.zora.co/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'Catalog',
    'query': """
      query Catalog {
        Currency(where: {address: {_eq: "%s"}}) {
          address
          decimals
          symbol
        }
      }""" % contract_address,
    'variables': None
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['Currency']
  return (response[0]['symbol'].replace('WETH', 'ETH'), response[0]['decimals'])

### TWITTER ########################################################################################

def tweet_auction_started(record, id, contract_address):
  name = records[(id, contract_address)]['title']
  artist = get_username(record['minter'])
  bid = int(record['auctions'][0]['lastBidAmount']) / \
      10**record['auctions'][0]['currency']['decimals']
  bidder = get_username(record['auctions'][0]['lastBidder'])
  url = 'https://beta.catalog.works/%s/%s' % \
      (record['minter'], records[(id, contract_address)]['short_url'])

  tweet = """Reserve price met!

"%s" by %s

Current bid: %s ETH by %s

%s""" % (name, artist, bid, bidder, url)

  print(tweet)
  twitter.update_status(tweet)

def tweet_sale(record, id, contract_address, event):
  name = records[(id, contract_address)]['title']
  artist = get_username(record['minter'])
  collector = get_username(record['owner'])

  if event == 'market':
    currency = get_currency(record['media']['askEvents'][0]['currency'])
    price = int(record['media']['askEvents'][0]['amount']) / 10**currency[1]
    currency = currency[0]
  elif event == 'asks':
    currency = get_currency(record['v3Events'][0]['details']['askCurrency'])
    price = int(record['v3Events'][0]['details']['askPrice']) / 10**currency[1]
    currency = currency[0]
  elif event == 'auction':
    price = int(record['auctions'][0]['lastBidAmount']) / \
        10**record['auctions'][0]['currency']['decimals']
    currency = record['auctions'][0]['currency']['symbol'].replace('WETH', 'ETH')

  usd = '(%s)' % locale.currency(price * eth_price, grouping=True) if currency == 'ETH' else ''
  url = 'https://beta.catalog.works/%s/%s' % \
      (record['minter'], records[(id, contract_address)]['short_url'])

  tweet = """💽 %s 💽

✨ Record by %s
💰 Sold to %s for %s %s %s

%s""" % (name, artist, collector, price, currency, usd, url)

  print(tweet)
  twitter.update_status(tweet)

####################################################################################################

load_dotenv()
r = redis.from_url(os.environ['REDIS_URL'])
locale.setlocale(locale.LC_ALL, '')

auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET_KEY'])
auth.set_access_token(os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])
twitter = tweepy.API(auth)

eth_price = get_eth_price()
last_block_number = int(r.get('last_block_number')) + 1

try:
  records = get_catalog_records()

  for id, contract_address in get_zora_bid_events(last_block_number):
    tweet_auction_started(get_catalog_record(id, contract_address), id, contract_address)

  for id, contract_address, event in get_zora_sales(last_block_number):
    tweet_sale(get_catalog_record(id, contract_address), id, contract_address, event)
except Exception as e:
  send_discord_notification(traceback.format_exc())
