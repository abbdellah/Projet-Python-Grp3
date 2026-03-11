def test_process_after_one_success(client):
    # 1) créer une tentative
    r = client.post(
        "/attempts",
        json={
            "id_exercice_ou_evenement": 101,
            "id_apprenant": 1,
            "id_aav_cible": 1,
            "score_obtenu": 0.95,
            "est_valide": True,
            "temps_resolution_secondes": 30,
            "metadata": {"source": "pytest"},
        },
    )
    assert r.status_code == 201
    attempt_id = r.json()["id"]

    # 2) process
    r2 = client.post(f"/attempts/{attempt_id}/process")
    assert r2.status_code == 200

    data = r2.json()
    assert data["tentative_id"] == attempt_id
    assert data["id_apprenant"] == 1
    assert data["id_aav_cible"] == 1
    assert 0.0 <= data["nouveau_niveau"] <= 1.0
    assert isinstance(data["message"], str)