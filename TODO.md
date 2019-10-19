# A TODO List!

## Required Functionality

### Story Processing/Running summarization

* Research the appropriate background task framework to implement arbitrary
  workers. Here are some possible options:
  * Redis queue or async redis queue?
  * Celery?
* Figure out the appropriate table/column structure to support processing
  stories. Here are some important factors:
  * Support aggregating based on a story's game_pid
  * Start with just scene entries, but might need to break out by challenges,
    cards, and characters as well
  * Easy way to determine what new text to preprocess (run summarization on)
  * Need to be able to support selecting last N entries in chronological order
  * Possible columns: json, hash, status, entry_number, result
    * status should indicate whether preprocessing is complete
    * result holds the output of the preprocessing
    * entry_number should define a total ordering across scenes, but should not
      be unique, in case it is revised and we have two different hashes for the
      same entry
* Implement basic task framework and execution


### Generating suggestions

* Figure out best way to integrate external code and models into the build and
  deployment setup. Want to isolate components such that you can easily pull
  the latest trained model and code.
  * Look into the possibility of creating a Docker registry to hold the various
    models. Each would be a web service you call into to get a result.
* Figure out how to include Service Streamer to batch requests to the model
* Create a table to hold suggestions. Potential columns:
  * story_hash, suggestion_type, model_used, suggestion, status
* Need a way to send partially generated suggestions to be stored in the db


## Advanced Functionality

* Support HTTPS and/or HMAC authentication to use the API
* Make the deployment approach be able to support deploying to other machines,
  including my home server, which has two TitanX's
* Use HMAC to generate the json hashes so that it cannot be easily reversed


## Improvements

* Include a staging environment in addition to dev & prod
* Improve production deploy workflow to reduce chance of losing data.
  Currently, there is a non-trivial possibilty of losing the production
  database.


## Documentation

* Write basic README.md to document how to use this repo, so you do not forget
  important processes or commands
* Create an interactive documentation website using mkdocs and the material
  theme
