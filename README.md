# Exchange Metadata Poller
## Setup
- Create and activate a virtual environment 
- Install requirements from requirement.txt (`pip install -r requirements.txt`)
- Add the required tokens to config.toml
- Run the poller from the project root (`python -m server.core`)
## Functionality
### Polling
- Polls the binance apis for info related to:
  - [Exchange Info](https://developers.binance.com/docs/binance-spot-api-docs/rest-api#exchange-information)
    - Rate limit info
    - Info for each trading pair:
      - Status (trading/break/etc)
      - Tick size
      - Lot size
      - Step size
      - Min/Max prices
      - Min/Max quantity
  - [Account Info](https://developers.binance.com/docs/binance-spot-api-docs/rest-api#account-information-user_data)
    - Maker/taker/buyer/seller commissions, rates, etc
    - Permissions (trade/withdraw/deposit/etc)
    - Balances
  - [System Status](https://binance-docs.github.io/apidocs/spot/en/#system-status-system)
    - Is the exchange operational?
### Data Service
- Provides a simple web API where one can request the various pieces of polled state.
### Persistence
- Stores historical record in the form of a log on disk. This contains all of the responses from the Binance API, useful for
    reconstructing past state.

## Things that really should be done, but the time limit did not allow
- **Deployment/Networking infrastructure**: This is a toy project, there are all manner of infrastruture things (auth, https, redundancy, clean shutdowns, etc)
    that must be done before something is ready for production deployment. 
- **Typing for responses:** the Binance API gives back a buch of string-string dictionaries everywhere. This makes
    the code hard to grok and is generally a recipe for disaster in the long run.
  - Related: **DOCS**. There are docstrings inline with many of the methods, but there is no comprehensive API documentation.
    This is obviously necessary for a production service.
- **Some sort of database for persistence**. Right now everything is stored in memory and dropped on the floor when we restart.
    If we were running multiple instances of the poller, they would not be consistent because they would each maintain individual state.
    This is remedied by moving the shared state into a shared database.
  - **Related: (partially implemented) historical record of configs and updates.** It's crucial for a production system that you have a complete
    historical record of config changes. It's really hard (sometimes impossible!) to debug any sort of production issue
    when you don't know for sure what configs were in play at the time of the incident. I added a publisher to write all 
    of the responses for each config update to disk, so we have the information necessary to do this time-travel, but
    the actual "give me the config that was authoritative at time _t_" is TODO.
- **Exception handling:** right now if something goes wrong, we don't necessarily recover. This is obviously not OK in real life.
- **Realtime Trading Status Updates** I skimmed the websocket api docs to see if there is a socket api that provides 
    trading status updates (https://dev.binance.vision/t/explanation-on-symbol-status/118) as they happen, but as far as
    I know, this does not exist. Knowing when certain pairs are halted could be time-critical information, so we'd need
    to come up with a way to synthesize this (maybe infer it from ticket updates?).
