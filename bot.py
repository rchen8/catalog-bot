import json
import requests

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
  return {int(track['nft_id']): track for track in response}

def get_zora_sales(last_block_number):
  url = 'https://indexer-prod-mainnet.zora.co/v1/graphql'
  headers = {
    'content-type': 'application/json'
  }
  payload = {
    'operationName': 'Catalog',
    'query': """
      query Catalog {
        MarketBidEvent(where: {status: {_eq: "FINALIZED"}, blockTimestamp: {_gt: "%s"}}) {
          amount
          blockTimestamp
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
        }
      }""" % address.lower(),
    'variables': None
  }
  response = requests.post(url, headers=headers, data=json.dumps(payload)).json()\
      ['data']['catalog_users']
  return response[0]['name'] if len(response) > 0 else None

def tweet(record, sale):
  name = record['title']
  artist = record['artist']['name']
  collector = get_username(sale['recipient'])
  price = int(sale['amount']) / 10**sale['currency']['decimals']
  currency = sale['currency']['symbol'].replace('WETH', 'ETH')
  handle = record['artist']['handle']
  url = record['short_url']

  tweet = """💽 %s 💽

✨ Record by %s
💰 Sold to %s for %s %s

https://beta.catalog.works/%s/%s""" % (name, artist, collector, price, currency, handle, url)

  print(tweet)

####################################################################################################

catalog_records = get_catalog_records()
zora_sales = get_zora_sales('2021-10-20')
for id in zora_sales:
  if id in catalog_records:
    tweet(catalog_records[id], zora_sales[id])
