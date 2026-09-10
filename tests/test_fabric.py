from fs_overlay.fabric import Node, ResourceFabric, ResourceOffer, ResourceRequest, ShareClass


def test_private_capacity_is_not_offerable():
    offer = ResourceOffer("o", "n", "cpu", 2, "cores", ShareClass.PRIVATE)
    assert "private resource cannot be offered to the fabric" in offer.validate()


def test_private_data_is_never_implicitly_shared():
    offer = ResourceOffer("o", "n", "storage", 100, "GB", ShareClass.SHARED, private_data_included=True)
    assert "private data cannot be implicitly shared" in offer.validate()


def test_fabric_requires_explicit_trust_and_admission():
    request = ResourceRequest("r", "user", "cpu", 1, "cores")
    offers = (
        ResourceOffer("untrusted", "n1", "cpu", 4, "cores", ShareClass.SHARED),
        ResourceOffer("trusted", "n2", "cpu", 2, "cores", ShareClass.LEASED),
    )
    nodes = (
        Node("n1", "linux", frozenset({"cpu"}), frozenset({ShareClass.SHARED}), trusted=False),
        Node("n2", "windows", frozenset({"cpu"}), frozenset({ShareClass.LEASED}), trusted=True),
    )
    matches = ResourceFabric().match(request, offers, nodes)
    assert [offer.offer_id for offer in matches] == ["trusted"]
