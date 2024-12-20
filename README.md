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
}
```

