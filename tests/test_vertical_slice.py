from fs_overlay.federation import SimulatedFederation, SimulatedNode
from fs_overlay.ir import CapabilityRequirement, IRKind, ResourceRequirement, SemanticIR
from fs_overlay.matching import CapabilityOffer, match_capabilities
from fs_overlay.presentation import PresentationEndpoint, PresentationKind
from fs_overlay.session import ApplicationSession, MobilityClass, SessionState


def test_ir_validation_rejects_incomplete_plan() -> None:
    ir = SemanticIR(kind=IRKind.PLAN, ir_id="p1", operation="run")
    assert "non-intent IR requires target" in ir.validate()
    assert "plan requires verification conditions" in ir.validate()


def test_capability_matching_is_deterministic() -> None:
    result = match_capabilities(
        (CapabilityRequirement("cpu", minimum=4, unit="cores"), CapabilityRequirement("gpu")),
        (CapabilityOffer("cpu", capacity=8, unit="cores"),),
    )
    assert not result.matched
    assert result.missing == ("gpu",)


def test_optional_capability_does_not_block() -> None:
    result = match_capabilities(
        (CapabilityRequirement("gpu", optional=True),),
        (),
    )
    assert result.matched


def test_session_separates_execution_and_presentation() -> None:
    endpoint = PresentationEndpoint("android-display", PresentationKind.DISPLAY, "stream-v1", "android").admit()
    session = ApplicationSession("s1", "windows-app", "user1", MobilityClass.CHECKPOINTABLE, requirements=("windows-runtime",))
    session.bind_presentation(endpoint.endpoint_id)
    assert session.execution_node is None
    assert session.presentation_endpoint == "android-display"


def test_two_node_federation_places_remote_session() -> None:
    federation = SimulatedFederation(
        (
            SimulatedNode("android", (CapabilityOffer("android-runtime"),)),
            SimulatedNode("windows", (CapabilityOffer("windows-runtime"), CapabilityOffer("cpu", 8, "cores"))),
        )
    )
    session = ApplicationSession("s1", "photoshop-like", "user1", MobilityClass.CHECKPOINTABLE, requirements=("windows-runtime",))
    session.bind_presentation("android-display")
    assert federation.place(session) == "windows"
    assert federation.execute(session)["status"] == "succeeded"
    assert session.state is SessionState.RUNNING


def test_offline_node_is_not_selected() -> None:
    federation = SimulatedFederation((SimulatedNode("windows", (CapabilityOffer("windows-runtime"),), online=False),))
    session = ApplicationSession("s1", "app", "user1", MobilityClass.RESTARTABLE, requirements=("windows-runtime",))
    try:
        federation.place(session)
    except RuntimeError as exc:
        assert "no admitted node" in str(exc)
    else:
        raise AssertionError("offline node must not be selected")
