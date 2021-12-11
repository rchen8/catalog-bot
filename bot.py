from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
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
        nft_id
        short_url
        title
        __typename
    }"""
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()['data']['tracks']
  return {int(track['nft_id']): track for track in response if track['nft_id'] is not None}

def get_zora_sales(last_block_number):
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
  return {int(sale['tokenId']): sale for sale in response}

def get_zora_auction_started(last_block_number):
  url = 'https://indexer-prod-mainnet.zora.co/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'Catalog',
    'query': """
      query Catalog {
        AuctionBidEvent(where: {firstBid: {_eq: true}, blockNumber: {_gt: %s}}) {
          blockNumber
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
  return [int(bid['tokenId']) for bid in response]

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

def get_highest_bid(id):
  url = 'https://indexer-prod-mainnet.hasura.app/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'GetMediaById',
    'query': """
      query GetMediaById($tokenId: String!) {
        Media(where: {tokenId: {_eq: $tokenId}}) {
          auctions(order_by: {createdEvent: {blockNumber: desc}}) {
            lastBidAmount
            lastBidder
          }
        }
      }""",
    'variables': {'tokenId': id}
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['Media'][0]['auctions'][0]
  return int(response['lastBidAmount']) / 10**18, get_username(response['lastBidder'])

####################################################################################################

def tweet_auction_started(record):
  name = record['title']
  artist = get_username(record['artist']['id'])
  bid, username = get_highest_bid(record['nft_id'])
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
  collector = get_username(sale['recipient'])
  price = int(sale['amount']) / 10**18
  usd = locale.currency(price * eth_price, grouping=True)
  handle = record['artist']['handle']
  url = record['short_url']

  tweet = """💽 %s 💽

✨ Record by %s
💰 Sold to %s for %s ETH (%s)

https://beta.catalog.works/%s/%s""" % (name, artist, collector, price, usd, handle, url)

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
for id in auction_started:
  if id in catalog_records:
    tweet_auction_started(catalog_records[id])

zora_sales = get_zora_sales(last_block_number)
for id in zora_sales:
  if id in catalog_records:
    tweet_sale(catalog_records[id], zora_sales[id])
