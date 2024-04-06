import base58
import asyncio
import base64
import json
import time
import requests
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from jupiter_python_sdk.jupiter import Jupiter, Jupiter_DCA
from solana.transaction import Transaction
from solana.rpc.api import Client
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction
from solders.message import to_bytes_versioned
from solders.signature import Signature
from solana.rpc.commitment import Commitment
import re
from solana.rpc.api import RPCException

solscan_rpc = 'https://api.mainnet-beta.solana.com/'  # Use this RPC for transaction check
rpc_url = working_rpc  #OUIKNODE works well

async def try_jup_swap_data(input_mint: str, output_mint: str, amount: int, slippage_bps: int = 1000,
                    computeUnitPriceMicroLamports: int = 0):
    for i in range(0, 5):
        try:
            private_key = Keypair.from_bytes(base58.b58decode('YOUR_KEY'))  # Replace 'YOUR_KEY' with your private key
            async_client = AsyncClient(rpc_url)
            jupiter = Jupiter(async_client, private_key)

            if computeUnitPriceMicroLamports != 0:
                swap = await jupiter.swap(
                    input_mint=input_mint,
                    output_mint=output_mint,
                    amount=amount,
                    slippage_bps=slippage_bps,
                    computeUnitPriceMicroLamports=computeUnitPriceMicroLamports,
                )
                return swap
            else:
                swap = await jupiter.swap(
                    input_mint=input_mint,
                    output_mint=output_mint,
                    amount=amount,
                    slippage_bps=slippage_bps,
                )
                return swap
        except:
            continue
    return 0


async def send_swap(input_mint: str, output_mint: str, amount: int, slippage_bps: int = 1000,
                    computeUnitPriceMicroLamports: int = 0):

    private_key = Keypair.from_bytes(base58.b58decode(
        'YOUR_KEY'))  # Replace 'YOUR_KEY' with your private key

    swap = await try_jup_swap_data(input_mint=input_mint, output_mint=output_mint, amount=amount, slippage_bps=slippage_bps,
                                       computeUnitPriceMicroLamports=computeUnitPriceMicroLamports)

    if not swap:
        return 3

    raw_tx = VersionedTransaction.from_bytes(base64.b64decode(swap))
    signature = private_key.sign_message(to_bytes_versioned(raw_tx.message))
    signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])

    txid = ''
    ctx = AsyncClient(
        rpc_url,
        commitment=Commitment("confirmed"), timeout=30)

    for i in range(0, 50):
        txid = "sending Tx failed"
        try:
            txid = (await ctx.send_transaction(
                signed_tx
            ))

            txid = txid.to_json()
            txid = json.loads(txid)
            txid = str(txid['result']).replace("[", "").replace("]", "").replace("'", "")  # can be made better :)
        except:
            continue

        return check(txid)


def safe_swap(input_mint: str, output_mint: str, amount: int, slippage_bps: int = 1000,
              computeUnitPriceMicroLamports: int = 0):
    for i in range(0, 5):
        result = asyncio.run(send_swap(input_mint=input_mint, output_mint=output_mint, amount=amount, slippage_bps=slippage_bps,
                                       computeUnitPriceMicroLamports=computeUnitPriceMicroLamports))
        if (result == 2):
            print("Failed to get status response (but transaction may be successful)")
            return 2
        if (result == 3):
            print("Failed to get Tx data from jupiter")
            return 3
        elif result != 1:
            return result

    return "Safe swap failed"


def get_response(txid):
    rpc_query = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [txid, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
    }

    for i in range(0, 5):
        try:
            response = requests.post(solscan_rpc, json=rpc_query)
            return response
        except:
            continue
    print("Failed to get response")
    return 0


def check(txid):
    for i in range(0, 25):
        response = get_response(txid)
        if not response:
            return 2

        if response.json()["result"]:
            return txid
        else:
            print("Checking transaction status...")
            time.sleep(5)  # 25*5s = ~300 blocks
    print("Transaction did not occur")
    return 1


###################  Example of use #########################
print(safe_swap(input_mint="F23fFqpRNsmWjuUrFpfM1pvoVvMSpLuN6hY978Y1JXLt",
                output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                amount=69247))
