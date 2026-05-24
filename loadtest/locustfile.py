from locust import HttpUser, between, task


class ChatCompletionUser(HttpUser):
    wait_time = between(0.2, 1.5)

    @task
    def chat_completion(self) -> None:
        self.client.post(
            "/v1/chat/completions",
            json={
                "model": "resume-llm",
                "messages": [
                    {"role": "system", "content": "Answer like a concise SRE."},
                    {"role": "user", "content": "How do you detect inference latency regressions?"},
                ],
                "max_tokens": 128,
            },
        )
