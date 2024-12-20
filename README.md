# Smoq Bot: Automating Trades Using REST API

The **Smoq Bot** is an advanced Python-based tool designed to automate trading operations in **SMOQ Games 25**. It leverages **REST API** endpoints to interact with the game's backend, handling tasks like user authentication, sending trade invitations, managing responses, and conducting trades.

---

## Features

- **Fully REST API-Driven**: The bot communicates exclusively with the game's backend using HTTP requests.
- **Dynamic Token Refreshing**: Ensures seamless operation without manual intervention.
- **Asynchronous Design**: Handles multiple trades efficiently using Python's `asyncio` library.
- **Wishlist Management**: Retrieves and processes user wishlist data to tailor trade proposals.
- **Customizable**: Easily configure the number of trades, invitation codes, and more.

---

## How It Works

### 1. **Authentication and Token Management**
The bot starts by refreshing its access token using Firebase's REST API:
- **Endpoint**: `https://securetoken.googleapis.com/v1/token?key=<FIREBASE_API_KEY>`
- **Method**: `POST`
- **Purpose**: Obtain a fresh access token using the provided refresh token.
- **Payload**:
  ```json
  {
      "grant_type": "refresh_token",
      "refresh_token": "<REFRESH_TOKEN>"
  }
  ```

### 2. Sending Trade Invitations
The bot sends a trade invitation to initiate a session:
- **Endpoint**: `https://europe-west2-smoqgames25-simulation.cloudfunctions.net/addTradeInvitation`
- **Method**: `POST`
- **Purpose**: Starts a trade session with a specific invitation code.
- **Payload**:
  ```json
  {
    "data": {
        "name": "<TRADE_NAME>",
        "uid2": "<BOT_UID>",
        "badgeId": 10000,
        "code": "<INVITATION_CODE>",
        "version": 21
    }
    ```

### 3. Monitoring User Responses
The bot listens for user responses to the trade invitation:
- **Endpoint**: `https://firestore.googleapis.com/v1/projects/smoqgames25-simulation/databases/(default)/documents/TResp3/<RESPONSE_KEY>`
- **Method**: `GET`
- **Purpose**: Checks if a user has accepted the trade invitation.
- **Retry Mechanism**: Implements exponential backoff for retries, checking periodically for updates.
If the user accepts, the bot retrieves the trade ID and the opponent's UID for the next steps.

### 4. Fetching Wishlist
The bot retrieves the opponent's wishlist to customize trade proposals:
- **Endpoint**: `https://firestore.googleapis.com/v1/projects/smoqgames25-simulation/databases/(default)/documents/Trade3/<TRADE_ID>`
- **Method**: `GET`
- **Purpose**: Fetches wishlist data to determine which cards the opponent is interested in.
If no wishlist is found, the bot uses a default list of cards to propose a trade.

### 5. Proposing a Trade
Once the wishlist is retrieved, the bot sends a trade proposal:
- **Endpoint**: `https://firestore.googleapis.com/v1/projects/smoqgames25-simulation/databases/(default)/documents/Trade3/<TRADE_ID>/<PATH>`
- **Method**: `PATCH`
- **Purpose**: Sends card offers and proposals based on the opponent's wishlist.
- **Payload Example**:
```json
{
    "fields": {
        "m": {
            "arrayValue": {
                "values": [
                    {"integerValue": "80"},  // Message Type
                    {"integerValue": "0"}, 
                    {"integerValue": "100000"},
                    {"integerValue": "0"},
                    {"integerValue": "<CARD_ID_1>"},
                    {"integerValue": "1"},
                    {"integerValue": "<CARD_ID_2>"},
                    {"integerValue": "1952"}
                ]
            }
        },
        "timestamp": {"timestampValue": "<ISO_TIMESTAMP>"}
    }
}
```

### 6. Confirming and Finalizing the Trade
After a proposal is accepted, the bot confirms and finalizes the trade:
- **Endpoint**: `https://europe-west2-smoqgames25-simulation.cloudfunctions.net/confirmAndCheckTrade`
- **Method**: `POST`
- **Purpose**: Confirms the trade with the agreed terms and checks the final result.
- **Payload Example**:
```json
{
    "data": {
        "tradeId": "<TRADE_ID>",
        "cardGuids": ["<GUID_1>", "<GUID_2>", "<GUID_3>"],
        "coins": {
            "@type": "type.googleapis.com/google.protobuf.Int64Value",
            "value": 101526
        },
        "name": "Bot",
        "diff": {
            "@type": "type.googleapis.com/google.protobuf.Int64Value",
            "value": 100000
        }
    }
}
```


