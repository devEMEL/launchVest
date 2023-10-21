import json
from algosdk.v2client.algod import AlgodClient


def asset_info(algod_client: AlgodClient, address: str, asset_id: int) -> None:
    account_info = algod_client.account_info(address)
    idx = 0
    for my_account_info in account_info['created-assets']:
        scrutinized_asset = account_info['created-assets'][idx]
        idx += 1       
        if scrutinized_asset['index'] == asset_id:
            print("Asset ID: {}".format(scrutinized_asset['index']))
            print(json.dumps(my_account_info['params'], indent=4))
            break


def asset_holding_info(algod_client: AlgodClient, address: str, asset_id: int) -> None:
    account_info = algod_client.account_info(address)
    print(f"""New fields
        address: {address},
        asset info for {address} {algod_client.account_asset_info(address, asset_id)}
    """)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx += 1
        if scrutinized_asset['asset-id'] == asset_id:
            print(f"Asset ID {scrutinized_asset['asset-id']}")
            print(f"{json.dumps(scrutinized_asset, indent=4)}")
            break
