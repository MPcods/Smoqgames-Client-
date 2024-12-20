import aiohttp
import logging
import asyncio
import random
from enum import Enum
from datetime import datetime, timezone

# Logger Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

REFRESH_TOKEN = "AMf-vBzNoE9PrgRurqCitdWG-RIDeObPVsue67mlYJ4RHUkOl23bl3GxogVf_PRseHuJ24ETk_tOd98pujr_m1jIbl_tCP30v0-i9JKzVhh8fZOMq6ytzDeuSO9qaZ7__WJEDz6jh6gO6cmxYVB6HDp1AgWWtG1-HeMcEKMK9A9lzlvfvY0D2Y8ileKLzu17DamvZ8763TxFVVHwxzCfYb4lj5CmJh6W3L5Ck1Qtv5YnZvMumQcQubHVs77LfrGNiKziZ2TetGBLKSqZcyx0Txg3xRU4MLBEdjj9rYNubn-pgk1u1ivseAaAQH_USnxi_zTj_0E2k8GPpHPT4H3HarJMLX9n8UFti1ZJ00M-OMwhLdmSSFTdlrWD57KBnIUOR-4QJkeWQNv6_pDBjLB63HyBumRvbKiD_byO0MhHSr0riF5mcLiVA86o_f3kRyyywZtU2mUIMpwf"
FIREBASE_API_KEY = "AIzaSyATJBW3UtO7AUKVUVeNVsntxd4RZFdRPcs"
URL_INVITE = "https://europe-west2-smoqgames25-simulation.cloudfunctions.net/addTradeInvitation"
URL_HELLOMSG = "https://europe-west2-smoqgames25-simulation.cloudfunctions.net/sendHelloMessage"
URL_FIRESTORE_PATCH = "https://firestore.googleapis.com/v1/projects/smoqgames25-simulation/databases/(default)/documents/Trade3/"
URL_TRESP = "https://firestore.googleapis.com/v1/projects/smoqgames25-simulation/databases/(default)/documents/TResp3/"
BOT_UID = "a_7353099967007399487"
URL_REFRESH = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"

class MessageTypes(Enum):
    PROPOSAL = "80"
    MONEY = "77"
    CHAT_MESSAGE = "66"
    TRADE_ACCEPT = "65"
    TRADE_CONFIRM = "67"
    LEAVE_TRADE = "76"
    SEND_CARDS = "88"
    REJECT_TRADE = "82"
    REMOVE_CARD = "68"

class Bot:
    def __init__(self, inv_code: str, trade_count: int, session: aiohttp.ClientSession):
        print("""
        + ------------------------------------------------------ +
                    SMOQ BOT BY MARCC & TATRIX
        + ------------------------------------------------------ +
        """)
        self.inv_code = inv_code
        self.trade_count = trade_count 
        self.bot_uid = BOT_UID
        self.session = session
        self.access_token = None

    def set_headers(self):
        self.headers_invite = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "x-firebase-appcheck": "eyJlcnJvciI6IlVOS05PV05fRVJST1IifQ==",
            "user-agent": "grpc-java-okhttp/1.52.1",
        }
        self.headers_firestore = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def create(cls, inv_code: str, trade_count):
        session = aiohttp.ClientSession()
        self = cls(inv_code, trade_count, session)
        self.access_token = await self.generate_access_token()
        self.set_headers()
        return self

    async def generate_access_token(self):
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        }
        headers = {"Content-Type": "application/json"}
        async with self.session.post(URL_REFRESH, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("access_token")
            else:
                logging.error(f"Failed to refresh access token: {response.status} {await response.text()}")
                return None


        self.start_trading_loop()


    async def start_trading_loop(self):
        while self.trade_count > 0:
            logging.info(f"Remaining trades: {self.trade_count}")
            try:
                response_key = await self.send_invite()
                trade_id, opponent_uid = await self.wait_for_user_response(response_key)

                await self.start_trade(trade_id, opponent_uid)

                self.trade_count -= 1

                if self.trade_count == 0:
                    logging.info("All trades completed. Ending process.")
                    break

            except TimeoutError as te:
                logging.error(f"Timeout error: {te}. Skipping this trade.")
                self.trade_count -= 1

            except Exception as e:
                logging.error(f"Unexpected error during trade process: {e}. Skipping this trade.")
                self.trade_count -= 1

            await asyncio.sleep(0.5)

    # Schritt 1: Sende Einladung
    async def send_invite(self):
        data = {
        "data": {
            "name": f"SE{self.trade_count}",
            "uid2": self.bot_uid,
            "badgeId": 10000,
            "code": self.inv_code,
            "version": 21,
        }
    }
        async with self.session.post(URL_INVITE, json=data, headers=self.headers_invite) as response:
            if response.status == 200:
                logging.info("Invite sent successfully")
                response_data = await response.json()
                return response_data["result"]["responseKey"]
            else:
                logging.error(f"Failed to send invite: {response.status} {await response.text()}")
                raise Exception("Invite konnte nicht gesendet werden.")

    # Schritt 2: Warte auf Antwort des Users
    async def wait_for_user_response(self, response_key: str, max_retries: int = 60, initial_retry_interval: int = 1):
        url_tresp = f"{URL_TRESP}{response_key}"
        logging.info(f"Listening for user response at {url_tresp}...")
        retry_interval = initial_retry_interval

        for attempt in range(max_retries):
            async with self.session.get(url=url_tresp, headers=self.headers_firestore) as response:
                if response.status == 200:
                    response_data = await response.json()
                    logging.info(f"Response data: {response_data}")
                    if "fields" in response_data and "matchId" in response_data["fields"]:
                        trade_data = response_data["fields"]
                        trade_id = trade_data["matchId"]["stringValue"]
                        opponent_uid = trade_data["uid"]["stringValue"]
                        logging.info(f"User accepted the invite. Trade ID: {trade_id}, Opponent UID: {opponent_uid}")
                        return trade_id, opponent_uid
                elif response.status == 404:
                    logging.info(f"No response yet. Retrying in {retry_interval} seconds... (Attempt {attempt + 1}/{max_retries})")
                else:
                    logging.error(f"Unexpected error: {response.status} {await response.text()}")

            await asyncio.sleep(retry_interval)
            retry_interval = min(retry_interval * 2, 90)  # Exponentielles Backoff (maximal 90 Sekunden)

        logging.error(f"Failed to get user response after {max_retries} attempts.")
        raise TimeoutError("No user response received within the timeout period.")


    # Schritt 3: Starte den Trade
    async def start_trade(self, trade_id: str, opponent_uid: str):
        logging.info(f"Trade started. Sending Hello Message...")
        await self.send_hello_message(trade_id, opponent_uid)  # Asynchroner Aufruf
        wishlist = await self.obtener_wishlist(trade_id)  
        if not wishlist:
            logging.warning("Using default wishlist as none was retrieved.")
        await self.perform_patch_update(trade_id, opponent_uid)  # Asynchroner Aufruf
        await self.confirm_and_check_trade(trade_id)

    async def send_hello_message(self, trade_id: str, opponent_uid: str):
        data = {
            "data": {
                "name": "Marcc",
                "tradeKey": trade_id,
                "badgeId": 1000,
                "wishlist": [],
                "opponentUid": opponent_uid,
            }
        }
        async with self.session.post(URL_HELLOMSG, json=data, headers=self.headers_invite) as response:
            if response.status == 200:
                logging.info("Hello Message sent successfully.")
            else:
                logging.error(f"Failed to send Hello Message: {response.status} {await response.text()}")


    async def obtener_wishlist(self, trade_id: str, max_retries: int = 10, retry_interval: int = 2):
        default_card_id = 319187  
        url = f"{URL_FIRESTORE_PATCH}{trade_id}/9TyKm3RCUbMbvhiVh7jfXb8udS73"
        logging.info(f"Fetching wishlist from {url}...")

        for attempt in range(max_retries):
            async with self.session.get(url, headers=self.headers_firestore) as response:
                if response.status == 200:
                    wishlist_data = await response.json()
                    logging.info(f"Complete wishlist response: {wishlist_data}")

                    try:
                        documents = wishlist_data.get("documents", [])
                        if not documents:
                            logging.warning("No documents found in wishlist response.")
                            continue

                        fields = documents[0].get("fields", {})
                        wishlist_array = (
                            fields.get("wishlist", {})
                            .get("arrayValue", {})
                            .get("values", [])
                        )
                        wishlist = [int(item.get("integerValue", 0)) for item in wishlist_array]

                        if not wishlist:
                            logging.warning("No wishlist found. Using default card.")
                            return [default_card_id] * 5

                        if len(wishlist) < 5:
                            logging.info(f"Wishlist has less than 5 cards: {wishlist}")
                            while len(wishlist) < 5:
                                wishlist.append(wishlist[len(wishlist) % len(wishlist)])

                        if len(wishlist) > 5:
                            logging.info(f"Wishlist has more than 5 cards, truncating: {wishlist}")
                            wishlist = wishlist[:5]

                        logging.info(f"Final wishlist: {wishlist}")
                        return wishlist

                    except Exception as e:
                        logging.error(f"Error while extracting wishlist: {e}")
                        return [default_card_id] * 5

                else:
                    logging.warning(f"Wishlist not found yet. Retrying in {retry_interval} seconds... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_interval)

        logging.error("Failed to fetch wishlist after multiple retries. Using default cards.")
        return [default_card_id] * 5
        

    async def perform_patch_update(self, trade_id: str, opponent_uid: str):
        def gen_path():
            return "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(20))

        wishlist = await self.obtener_wishlist(trade_id)

        patch_urls = [
            f"{URL_FIRESTORE_PATCH}{trade_id}/{opponent_uid}/{gen_path()}",
            f"{URL_FIRESTORE_PATCH}{trade_id}/{opponent_uid}/{gen_path()}",
            f"{URL_FIRESTORE_PATCH}{trade_id}/{opponent_uid}/{gen_path()}",
            f"{URL_FIRESTORE_PATCH}{trade_id}/{opponent_uid}/9TyKm3RCUbMbvhiVh7jfXb8udS73",
            f"{URL_FIRESTORE_PATCH}{trade_id}/{opponent_uid}/{gen_path()}",
        ]
        message_types = [
            MessageTypes.SEND_CARDS,
            MessageTypes.CHAT_MESSAGE,
            MessageTypes.PROPOSAL,
            MessageTypes.TRADE_ACCEPT,
            MessageTypes.TRADE_CONFIRM,
        ]

        for url, message_type in zip(patch_urls, message_types):
            if message_type == MessageTypes.TRADE_CONFIRM:
                logging.info("Waiting 3 seconds before sending TRADE_CONFIRM...")
                await asyncio.sleep(3)
            else:
                logging.info(f"Waiting 0.5 seconds before sending patch for {message_type}...")
                await asyncio.sleep(1.5)

            # Sende den Patch
            data = self.generate_patch_data(message_type, wishlist if message_type in [MessageTypes.SEND_CARDS, MessageTypes.PROPOSAL] else None)
            async with self.session.patch(url, json=data, headers=self.headers_firestore) as response:
                if response.status == 200:
                    logging.info(f"Patch successful for {message_type} at {url}")
                else:
                    logging.error(f"Failed to patch {message_type} at {url}: {response.status} {await response.text()}")
            

    def generate_patch_data(self, message_type: MessageTypes, wishlist=None):
        #  SEND_CARDS und PROPOSAL
        if message_type in [MessageTypes.SEND_CARDS, MessageTypes.PROPOSAL]:
            return {
                "fields": {
                    "m": {
                        "arrayValue": {
                            "values": [
                                {"integerValue": str(message_type.value)},  # Nachrichtentyp für SEND_CARDS/PROPOSAL
                                {"integerValue": "0"}, 
                                {"integerValue": "100000"},
                                {"integerValue": "0"},
                                {"integerValue": wishlist[0] if wishlist else 0},
                                {"integerValue": "1"},
                                {"integerValue": wishlist[1] if wishlist else 0},
                                {"integerValue": "1952"},
                                {"integerValue": wishlist[2] if wishlist else 0},
                                {"integerValue": "3"},
                                {"integerValue": wishlist[3] if wishlist else 0},
                                {"integerValue": "1954"},
                                {"integerValue": wishlist[4] if wishlist else 0},
                                {"integerValue": "1953"},
                            ]
                        }
                    },
                    "timestamp": {"timestampValue": datetime.now(timezone.utc).isoformat()},
                }
            }
        elif message_type in [MessageTypes.CHAT_MESSAGE]:
            return {
                "fields": {
                    "m": {
                        "arrayValue": {
                            "values": [
                                {"integerValue": "66"},  # Nachrichtentyp für SEND_CARDS/PROPOSAL
                                {"integerValue": "0"}, 
                                {"integerValue": "0"}, 
                                {"integerValue": "0"},                                  
                            ]
                        }
                    },

                    "timestamp": {"timestampValue": datetime.now(timezone.utc).isoformat()},
                    "2": {"integerValue": "1"}
  }
}
        # Daten für TRADE_ACCEPT
        elif message_type == MessageTypes.TRADE_ACCEPT:
            return {
                "fields": {
                    "m": {
                        "arrayValue": {
                            "values": [
                                {"integerValue": "65"},  # Nachrichtentyp
                                {"integerValue": "0"},
                                {"integerValue": "0"},
                                {"integerValue": "0"},
                            ]
                        }
                    },
                    "timestamp": {"timestampValue": datetime.now(timezone.utc).isoformat()},
                }
            }
        # Daten für TRADE_CONFIRM
        elif message_type == MessageTypes.TRADE_CONFIRM:
            return {
                "fields": {
                    "m": {
                        "arrayValue": {
                            "values": [
                                {"integerValue": "67"},  # Nachrichtentyp
                                {"integerValue": "0"},
                                {"integerValue": "0"},
                                {"integerValue": "0"},
                            ]
                        }
                    },
                    "timestamp": {"timestampValue": datetime.now(timezone.utc).isoformat()},
                }
            }
        else:
            raise ValueError(f"Unsupported message type: {message_type}")

    async def execute_patch(self, patch_url: str, data: dict):
        async with self.session.patch(url=patch_url, json=data, headers=self.headers_firestore) as response:
            if response.status == 200:
                logging.info(f"Patch successful for {patch_url}")
            else:
                error_text = await response.text()
                logging.error(f"Failed to patch {patch_url}: {response.status} {error_text}")

    def confirm_and_check_trade(self, trade_id: str):
    # 5 GUIDs
        def generate_guids(count: int = 5):
            return [generate_guids() for _ in range(count)]

        url = "https://europe-west2-smoqgames25-simulation.cloudfunctions.net/confirmAndCheckTrade"

        headers = {
        "Authorization": f"Bearer {self.access_token}",
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "User-Agent": "okhttp/3.12.13",
    }

    # Generiere die GUIDs
        card_guids = generate_guids()

        data = {
        "data": {
            "oppCardsIds": [],
            "bestOverall": 87,
            "ppp": 113,  
            "rrr": True,  
            "coins": {
                "@type": "type.googleapis.com/google.protobuf.Int64Value",
                "value": 101526
            },
            "name": "Bot",
            "cardGuids": card_guids,  
            "diff": {
                "@type": "type.googleapis.com/google.protobuf.Int64Value",
                "value": 100000
            },
            "cardIds": [],
            "quickSellCoins": {
                "@type": "type.googleapis.com/google.protobuf.Int64Value",
                "value": 1526
            },
            "tradeId": trade_id,
            "howManyWithBestOverall": 13
        }
    }

        logging.info(f"Confirming and checking trade {trade_id} with GUIDs {card_guids}...")

        response = self.session.post(url, json=data, headers=headers)

        if response.status_code == 200:
            logging.info(f"Trade {trade_id} confirmed successfully: {response.json()}")
        else:
            logging.error(f"Failed to confirm trade {trade_id}: {response.status_code} {response.text}")
   

if __name__ == "__main__":
    async def main():
        bot = await Bot.create(
            inv_code="NBM8LH",
            trade_count=3
        )
        try:
            await bot.start_trading_loop()
        finally:
            await bot.session.close()  # Schließe die Session explizit

    asyncio.run(main())