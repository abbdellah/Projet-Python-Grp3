def test_process_bob_aav1_reaches_mastery_with_prof_data(client):
    # Bob = id_apprenant 2, AAV 1
    r = client.post(
        "/attempts",
        json={
            "id_exercice_ou_evenement": 101,
            "id_apprenant": 2,
            "id_aav_cible": 1,
            "score_obtenu": 0.90,
            "est_valide": True,
            "temps_resolution_secondes": 75,
            "metadata": {"source": "pytest_prof_db"},
        },
    )
    assert r.status_code == 201
    attempt_id = r.json()["id"]

    r2 = client.post(f"/attempts/{attempt_id}/process")
    assert r2.status_code == 200

    data = r2.json()
    assert data["tentative_id"] == attempt_id
    assert data["id_apprenant"] == 2
    assert data["id_aav_cible"] == 1
    assert data["ancien_niveau"] == 0.85
    assert data["nouveau_niveau"] == 1.0
    assert data["est_maitrise"] is True