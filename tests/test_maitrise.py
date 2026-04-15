def test_mastery_reaches_one_after_5_successes(client):
    ids = []
    for i in range(5):
        r = client.post(
            "/attempts",
            json={
                "id_exercice_ou_evenement": 200 + i,
                "id_apprenant": 1,
                "id_aav_cible": 1,
                "score_obtenu": 0.95,  # >= 0.9
                "est_valide": True,
                "temps_resolution_secondes": 10,
                "metadata": None,
            },
        )
        assert r.status_code == 201
        ids.append(r.json()["id"])

    # Process la dernière tentative (ça recalculera sur toutes les tentatives)
    r2 = client.post(f"/attempts/{ids[-1]}/process")
    assert r2.status_code == 200
    data = r2.json()

    assert data["est_maitrise"] is True
    assert data["nouveau_niveau"] == 1.0