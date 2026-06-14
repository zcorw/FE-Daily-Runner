from typing import Any

import httpx


class QuestionBankError(RuntimeError):
    pass


class QuestionBankHTTPError(QuestionBankError):
    def __init__(self, method: str, path: str, status_code: int, body: str) -> None:
        self.method = method
        self.path = path
        self.status_code = status_code
        self.body = body
        super().__init__(f"{method} {path} failed with HTTP {status_code}: {body}")


class QuestionBankTimeoutError(QuestionBankError):
    def __init__(self, method: str, path: str, message: str) -> None:
        self.method = method
        self.path = path
        super().__init__(f"{method} {path} timed out: {message}")


class QuestionBankClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 20,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url + "/",
            timeout=timeout,
            transport=transport,
        )

    def health(self) -> dict[str, Any]:
        return self._request_json("GET", "/health")

    def keywords(self) -> dict[str, Any]:
        return self._request_json("GET", "/keywords")

    def candidates(self, **params: Any) -> dict[str, Any]:
        query = self._runtime_query_params(params)
        return self._request_candidates("GET", "/questions/candidates", params=query)

    def search_candidates(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_candidates("POST", "/questions/candidates/search", json=payload)

    def question_by_url(self, question_url: str) -> dict[str, Any]:
        return self._request_json("GET", "/questions/by-url", params={"url": question_url})

    def question(self, question_id: str) -> dict[str, Any]:
        return self._request_json("GET", f"/questions/{question_id}")

    def details_batch(
        self,
        urls: list[str],
        *,
        include_answer: bool,
        include_explanation: bool,
    ) -> dict[str, Any]:
        payload = {
            "urls": urls,
            "includeAnswer": include_answer,
            "includeExplanation": include_explanation,
        }
        return self._request_json("POST", "/questions/details/batch", json=payload)

    def asset_url(self, public_path: str) -> str:
        asset_path = public_path.removeprefix("/assets/fe-siken/").lstrip("/")
        return f"{self._base_url}/assets/fe-siken/{asset_path}"

    def close(self) -> None:
        self._client.close()

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise QuestionBankTimeoutError(method, path, str(exc)) from exc
        except httpx.RequestError as exc:
            raise QuestionBankError(f"{method} {path} request failed: {exc}") from exc

        if response.status_code >= 400:
            raise QuestionBankHTTPError(method, path, response.status_code, response.text)

        return response.json()

    def _request_candidates(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        payload = self._request_any_json(method, path, **kwargs)
        if isinstance(payload, list):
            return {"questions": [self._normalize_candidate(question) for question in payload]}
        if isinstance(payload, dict):
            questions = payload.get("questions")
            if isinstance(questions, list):
                return {
                    **payload,
                    "questions": [self._normalize_candidate(question) for question in questions],
                }
            return payload
        raise QuestionBankError(f"{method} {path} returned unexpected JSON type: {type(payload).__name__}")

    def _request_any_json(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise QuestionBankTimeoutError(method, path, str(exc)) from exc
        except httpx.RequestError as exc:
            raise QuestionBankError(f"{method} {path} request failed: {exc}") from exc

        if response.status_code >= 400:
            raise QuestionBankHTTPError(method, path, response.status_code, response.text)

        return response.json()

    @staticmethod
    def _normalize_candidate(question: Any) -> Any:
        if not isinstance(question, dict):
            return question
        if "url" in question or "questionUrl" not in question:
            return question
        return {**question, "url": question["questionUrl"]}

    @staticmethod
    def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in values.items() if value is not None}

    @classmethod
    def _runtime_query_params(cls, values: dict[str, Any]) -> dict[str, Any]:
        key_map = {
            "exam_part": "examPart",
        }
        return {key_map.get(key, key): value for key, value in cls._drop_none(values).items()}
