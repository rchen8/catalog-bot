from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
from web3 import Web3
import json
import locale
import os
import re
import redis
import requests
import tweepy

def get_eth_price():
  try:
    return CoinGeckoAPI().get_price(ids='ethereum', vs_currencies='usd')['ethereum']['usd']
  except:
    url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms=ETH&tsyms=USD'
    return requests.get(url).json()['ETH']['USD']

def is_catalog_contract(contract_address):
  return contract_address == '0x0bC2A24ce568DAd89691116d5B34DEB6C203F342'

def get_catalog_records():
  url = 'https://catalog-prod.hasura.app/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'GetTracks',
    'variables': {},
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
    }"""
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()['data']['tracks']
  return {(int(track['nft_id']), is_catalog_contract(track['contract_address'])):
      track for track in response if track['nft_id'] is not None}

def get_zora_auction_started(last_block_number):
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
          blockNumber: {_gt: %s},
          tokenContract: {_in: ["0x0bC2A24ce568DAd89691116d5B34DEB6C203F342", "0xabEFBc9fD2F806065b4f3C237d4b59D9A97Bcac7"]}
        }) {
          blockNumber
          tokenContract
          tokenId
          value
        }
      }""" % last_block_number,
    'variables': None
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['AuctionBidEvent']
  if len(response) > 0:
    r.set('last_block_number', max(int(r.get('last_block_number')),
        max([bid['blockNumber'] for bid in response])))
  return [(int(bid['tokenId']), is_catalog_contract(bid['tokenContract'])) for bid in response]

def get_market_events(last_block_number):
  url = 'https://indexer-prod-mainnet.zora.co/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'Catalog',
    'query': """
      query Catalog {
        MarketBidEvent(where: {status: {_eq: "FINALIZED"}, blockNumber: {_gt: %s}}) {
          amount
          blockNumber
          currency {
            decimals
            symbol
          }
          recipient
          tokenId
        }
      }""" % last_block_number,
    'variables': None
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['MarketBidEvent']
  if len(response) > 0:
    r.set('last_block_number', max(int(r.get('last_block_number')),
        max([sale['blockNumber'] for sale in response])))
  sales = {}
  for sale in response:
    sale['currency']['symbol'] = sale['currency']['symbol'].replace('WETH', 'ETH')
    sale['winner'] = sale['recipient']
    sales[(int(sale['tokenId']), False)] = sale
  return sales

def get_asks_events(last_block_number):
  address = '0x6170b3c3a54c3d8c854934cbc314ed479b2b29a3'
  topic0 = '0x21a9d8e221211780696258a05c6225b1a24f428e2fd4d51708f1ab2be4224d39'
  url = 'https://api.etherscan.io/api?' + \
      'module=logs&action=getLogs&fromBlock=%s&toBlock=latest&address=%s&topic0=%s&apikey=%s' % \
      (last_block_number, address, topic0, os.environ['ETHERSCAN_API_KEY'])
  sales = {}
  for event in requests.get(url).json()['result']:
    sale = {
      'amount': int(event['data'][322:], 16),
      'blockNumber': int(event['blockNumber'], 16),
      'auctionCurrency': Web3.toChecksumAddress('0x' + event['data'][218:258]),
      'winner': Web3.toChecksumAddress('0x' + event['topics'][3][-40:]),
      'tokenContract': Web3.toChecksumAddress('0x' + event['topics'][1][-40:])
    }
    if sale['tokenContract'] != '0xabEFBc9fD2F806065b4f3C237d4b59D9A97Bcac7':
      continue
    if sale['auctionCurrency'] == '0x0000000000000000000000000000000000000000':
      sale['auctionCurrency'] = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    sales[(int(event['topics'][2], 16), False)] = sale
    r.set('last_block_number', max(int(r.get('last_block_number')), sale['blockNumber']))
  return sales

def get_auction_events(last_block_number):
  url = 'https://indexer-prod-mainnet.zora.co/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'Catalog',
    'query': """
      query Catalog {
        AuctionEndedEvent(where: {
          blockNumber: {_gt: %s},
          tokenContract: {_eq: "0x0bC2A24ce568DAd89691116d5B34DEB6C203F342"}
        }) {
          amount
          auctionCurrency
          blockNumber
          tokenContract
          tokenId
          winner
        }
      }""" % last_block_number,
    'variables': None
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['AuctionEndedEvent']
  if len(response) > 0:
    r.set('last_block_number', max(int(r.get('last_block_number')),
        max([sale['blockNumber'] for sale in response])))
  return {(int(sale['tokenId']), True): sale for sale in response}

def get_zora_sales(last_block_number):
  return get_market_events(last_block_number) | \
         get_asks_events(last_block_number) | \
         get_auction_events(last_block_number)

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

def get_highest_bid(id, contract_address):
  url = 'https://indexer-prod-mainnet.hasura.app/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'GetTokenById',
    'query': """
      query GetTokenById($tokenId: String!, $tokenContractAddress: String!) {
        Token(where: {tokenId: {_eq: $tokenId}, address: {_eq: $tokenContractAddress}}) {
          auctions(order_by: {createdEvent: {blockNumber: desc}}) {
            lastBidAmount
            lastBidder
          }
        }
      }""",
    'variables': {'tokenId': id, 'tokenContractAddress': contract_address}
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['Token'][0]['auctions'][0]
  return int(response['lastBidAmount']) / 10**18, get_username(response['lastBidder'])

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

####################################################################################################

def tweet_auction_started(record):
  name = record['title']
  artist = get_username(record['artist']['id'])
  bid, username = get_highest_bid(record['nft_id'], record['contract_address'])
  handle = record['artist']['handle']
  url = record['short_url']

  tweet = """Reserve price met!

"%s" by %s

Current bid: %s ETH by %s

https://beta.catalog.works/%s/%s""" % (name, artist, bid, username, handle, url)

  print(tweet)
  twitter.update_status(tweet)

def tweet_sale(record, sale):
  name = record['title']
  artist = get_username(record['artist']['id'])
  collector = get_username(sale['winner'])
  currency, decimals = (sale['currency']['symbol'], sale['currency']['decimals']) \
      if 'currency' in sale else get_currency(sale['auctionCurrency'])
  price = int(sale['amount']) / 10**decimals
  usd = '(%s)' % locale.currency(price * eth_price, grouping=True) if currency == 'ETH' else ''
  handle = record['artist']['handle']
  url = record['short_url']

  tweet = """💽 %s 💽

✨ Record by %s
💰 Sold to %s for %s %s %s

https://beta.catalog.works/%s/%s""" % (name, artist, collector, price, currency, usd, handle, url)

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
catalog_records = get_catalog_records()
last_block_number = int(r.get('last_block_number'))

auction_started = get_zora_auction_started(last_block_number)
for id, version in auction_started:
  if (id, version) in catalog_records:
    tweet_auction_started(catalog_records[(id, version)])

zora_sales = get_zora_sales(last_block_number)
for id, version in zora_sales:
  if (id, version) in catalog_records:
    tweet_sale(catalog_records[(id, version)], zora_sales[(id, version)])
