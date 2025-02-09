INTENTS = [
    "INPUT_NAME",
    "CREATE_TRANSACTION",
    "UPDATE_TRANSACTION",
    "DELETE_TRANSACTION",
    "ANALYTICS_REQUEST",
    "MULTIPLE_TRANSACTIONS",
    "OTHER",
]

PROMPT_CLASSIFY_MESSAGE = """
    Read the below message/attached media and classify the intent of the message. Except for the case when intent is "OTHER", only reply with the exact intent category as it is.
    By default, if there is some transaction related detail, then it might be CREATE_TRANSACTION, but validate that it doesn't fall into any other category first.
    
    If you think that the intent is OTHER, then answer the question based on your knowledge.
    Intents: $intents
""".replace(
    "$intents", ", ".join(INTENTS)
)
