from locust import HttpUser, task, between
import random


class TodoUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.username = f"user_{random.randint(1, 100000)}"

        self.client.post("/register", params={
            "username": self.username,
            "password": "123"
        })

        response = self.client.post("/login", params={
            "username": self.username,
            "password": "123"
        })

        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def create_task(self):
        self.client.post("/tasks", params={
            "title": f"Задача {random.randint(1, 10000)}",
            "priority": random.randint(1, 10)
        }, headers=self.headers)

    @task(2)
    def get_tasks(self):
        self.client.get("/tasks", headers=self.headers)

    @task(1)
    def get_top_tasks(self):
        self.client.get("/tasks/top", headers=self.headers)

    @task(1)
    def search_tasks(self):
        self.client.get("/tasks", params={"search": "задача"}, headers=self.headers)
