from locust import HttpUser, task, between


class LoadTestUser(HttpUser):
    wait_time = between(0.9, 1.1)

    @task
    def post_item(self):
        payload = {"name": "sample_item", "price": 10.5}
        headers = {'Content-Type': 'application/json'}
        self.client.post("/item", json=payload, headers=headers)
