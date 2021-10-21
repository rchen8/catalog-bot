import json
import requests

url = 'https://indexer-prod-mainnet.zora.co/v1/graphql'
headers = {
  'content-type': 'application/json'
}
payload = {
  'operationName': 'Catalog',
  'query': """
query Catalog {
  Media(where: { metadata: { json: { _has_keys_all: ["body", "origin"]}}}) {
    contentHash
    contentURI
    creator
    creatorBidShare
    metadataHash
    metadataURI
    mintTransferEventId
    owner
    ownerBidShare
    prevOwner
    prevOwnerBidShare
    metadata {
      json
    }
  }
}""",
  'variables': None
}

response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(response)
