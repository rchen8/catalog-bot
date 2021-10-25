from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
import json
import locale
import os
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
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
  if len(response['data']['MarketBidEvent']) > 0:
    r.set('last_block_number',
        max([sale['blockNumber'] for sale in response['data']['MarketBidEvent']]))
  return {int(sale['tokenId']): sale for sale in response['data']['MarketBidEvent']}

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
    return
  for link in response[0]['links']:
    if link['type'] == 'TWITTER':
      return '@' + link['url'].replace('https://twitter.com/', '')
  return response[0]['name']

def tweet(record, sale):
  name = record['title']
  artist = record['artist']['name']
  collector = get_username(sale['recipient']) or sale['recipient'][0:6]
  price = int(sale['amount']) / 10**sale['currency']['decimals']
  currency = sale['currency']['symbol'].replace('WETH', 'ETH')
  usd = '(%s)' % (locale.currency(price * eth_price, grouping=True)) \
      if currency == 'ETH' else ''
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
zora_sales = get_zora_sales(int(r.get('last_block_number')))
for id in zora_sales:
  if id in catalog_records:
    tweet(catalog_records[id], zora_sales[id])
