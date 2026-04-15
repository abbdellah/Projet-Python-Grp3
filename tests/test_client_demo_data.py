from client.api_client import PlatonAAVClient
from client.demo_data import load_demo_dataset
from client.services import AAVService, AttemptService, LearnerService


class _TestSession:
    """Adapte le client FastAPI de test a l'interface attendue par requests."""

    def __init__(self, test_client):
        self.test_client = test_client

    def request(self, method, url, timeout=None, **kwargs):
        path = "/" + url.split("http://testserver/", 1)[-1]
        return self.test_client.request(method, path, **kwargs)


def test_demo_dataset_loads_through_api(client):
    http_client = PlatonAAVClient(
        base_url="http://testserver",
        session=_TestSession(client),
    )
    aav_service = AAVService(http_client)
    learner_service = LearnerService(http_client)
    attempt_service = AttemptService(http_client)

    result = load_demo_dataset(aav_service, learner_service, attempt_service)

    assert result.aavs == 5
    assert result.learners_created == 2
    assert result.attempts_created == 4

    aav_ids = {aav.id_aav for aav in aav_service.list_aavs(discipline="Informatique")}
    learner_names = {learner.nom_utilisateur for learner in learner_service.list_learners()}
    statuses = learner_service.get_learning_status(2001)

    assert {1001, 1002, 1003, 1004, 1005}.issubset(aav_ids)
    assert {"alice", "bob"}.issubset(learner_names)
    assert len(statuses) == 3
