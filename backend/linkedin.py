import requests


LINKEDIN_API = "https://api.linkedin.com/rest/posts"


def publish_to_linkedin(
    access_token: str,
    author_urn: str,
    text: str,
):

    headers = {
        "Authorization":
            f"Bearer {access_token}",

        "Content-Type":
            "application/json",

        "Linkedin-Version":
            "202604",

        "X-Restli-Protocol-Version":
            "2.0.0",
    }


    payload = {

        "author":
            author_urn,

        "commentary":
            text,

        "visibility":
            "PUBLIC",

        "distribution": {

            "feedDistribution":
                "MAIN_FEED",

            "targetEntities":
                [],

            "thirdPartyDistributionChannels":
                [],

        },

        "lifecycleState":
            "PUBLISHED",

        "isReshareDisabledByAuthor":
            False,

    }


    response = requests.post(

        LINKEDIN_API,

        headers=headers,

        json=payload,

        timeout=20,

    )


    response.raise_for_status()


    post_id = response.headers.get(
        "x-restli-id"
    )


    return {

        "success":
            True,

        "post_id":
            post_id,

        "response":
            response.json()
            if response.content
            else None

    }