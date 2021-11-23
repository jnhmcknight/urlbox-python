import json
import hmac
import requests
import urllib.parse
import validators
from hashlib import sha1
from urlbox import InvalidUrlException


class UrlboxClient:

    """
        The core client object used to interact with the Urlbox API

        :param api_key: Your API key found in your Urlbox Dashboard
        `https://urlbox.io/dashboard/api`

        :param api_secret: (Optional) Your API secret found in your Urlbox
        Dashboard`https://urlbox.io/dashboard/api`
        Required for authenticated requests.
    """

    BASE_API_URL = "https://api.urlbox.io/v1/"
    POST_END_POINT = "render"

    def __init__(self, *, api_key, api_secret=None, api_host_name=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_api_url = self._init_base_api_url(api_host_name)

    def get(self, options, to_string=False):
        """
            Make simple get request to Urlbox API

            :param options: dictionary containing all of the options you want to set.
            eg: {"url": "http://example.com/", "format": "png", "full_page": True, "width": 300}

            format: can be either "png", "jpg", "jpeg", "avif", "webp", "pdf", "svg", "html". Defaults to "png".

            :param to_string: (optional) if True, no request will be made to the API, instead a string
            representing the unauthenticaed get request URL will be returned.

            Example: urlbox_client.get({"url": "http://example.com/", "format": "png", "full_page": True, "width": 300})
            API example: https://urlbox.io/docs/getting-started
            Full options reference: https://urlbox.io/docs/options
        """

        if "html" not in options and "url" not in options:
            raise KeyError("Missing 'url' or 'html' key in options")

        if "url" in options:
            url = options["url"]

            url_stripped = url.strip()
            url_parsed = self._prepend_schema(url_stripped)
            options["url"] = url_parsed

            if not self._valid_url(url_parsed):
                raise InvalidUrlException(url_parsed)

        format = options.get("format", "png")
        options["format"] = format

        url_encoded_options = urllib.parse.urlencode(options)

        if to_string:
            return (
                f"{self.base_api_url}"
                f"{self.api_key}/{format}"
                f"?{url_encoded_options}"
            )

        if self.api_secret is None:
            return self._get_unauthenticated(format, url_encoded_options)
        else:
            return self._get_authenticated(format, url_encoded_options)

    def head(self, options):
        """
            Make simple head request to Urlbox API

            To get the response status/headers without pulling down the full response body.

            :param options: dictionary containing all of the options you want to set.
            eg: {"url": "http://example.com/", "format": "png", "full_page": True, "width": 300}

            format: can be either "png", "jpg", "jpeg", "avif", "webp", "pdf", "svg", "html". Defaults to "png".

            Example: urlbox_client.get({"url": "http://example.com/", "format": "png", "full_page": True, "width": 300})
            API example: https://urlbox.io/docs/getting-started
            Full options reference: https://urlbox.io/docs/options
        """

        if "html" not in options and "url" not in options:
            raise KeyError("Missing 'url' or 'html' key in options")

        if "url" in options:
            url = options["url"]

            url_stripped = url.strip()
            url_parsed = self._prepend_schema(url_stripped)
            options["url"] = url_parsed

            if not self._valid_url(url_parsed):
                raise InvalidUrlException(url_parsed)

        format = options.get("format", "png")
        options["format"] = format

        url_encoded_options = urllib.parse.urlencode(options)

        return requests.head(
            (
                f"{self.base_api_url}"
                f"{self.api_key}/{format}"
                f"?{url_encoded_options}"
            )
        )

    def post(self, options):
        """
              Make post request to Urlbox API

              :param options: dictionary containing all of the options you want to set.
              eg: {"url": "http://example.com/", "webhook_url": "http://yoursite.com/webhook", "format": "png", "full_page": True, "width": 300}

              format: can be either "png", "jpg", "jpeg", "avif", "webp", "pdf", "svg", "html". Defaults to "png".

              Example: urlbox_client.post({"url": "http://example.com/", "webhook_url": "http://yoursite.com/webhook", "format": "png", "full_page": True, "width": 300})
              Full options reference: https://urlbox.io/docs/options
          """

        if "html" not in options and "url" not in options:
            raise KeyError("Missing 'url' or 'html' key in options")

        if "webhook_url" not in options:
            raise KeyError("Missing 'webhook_url' key in options")

        if self.api_secret is None:
            raise Exception(
                "Missing api_secret when initialising client. Required for authorised post request."
            )

        if "url" in options:
            url = options["url"]

            url_stripped = url.strip()
            url_parsed = self._prepend_schema(url_stripped)
            options["url"] = url_parsed

            if not self._valid_url(url_parsed):
                raise InvalidUrlException(url_parsed)

        format = options.get("format", "png")
        options["format"] = format

        return requests.post(
            f"{self.base_api_url}{self.POST_END_POINT}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_secret}",
            },
            json=json.loads(json.dumps(options)),
        )

    # private

    def _get_authenticated(self, format, url_encoded_options):
        return requests.get(
            (
                f"{self.base_api_url}"
                f"{self.api_key}/{self._token(url_encoded_options)}/{format}"
                f"?{url_encoded_options}"
            )
        )

    def _get_unauthenticated(self, format, url_encoded_options):
        return requests.get(
            (
                f"{self.base_api_url}"
                f"{self.api_key}/{format}"
                f"?{url_encoded_options}"
            )
        )

    def _init_base_api_url(self, api_host_name):
        if api_host_name is None:
            return self.BASE_API_URL
        else:
            return f"https://{api_host_name}/"

    def _prepend_schema(self, url):
        if not url.startswith("http"):
            return f"http://{url}"
        else:
            return url

    def _token(self, url_encoded_options):
        return (
            hmac.new(
                str.encode(self.api_secret),
                str.encode(url_encoded_options),
                sha1,
            )
            .hexdigest()
            .rstrip("\n")
        )

    def _valid_url(self, url):
        return validators.url(url) == True
