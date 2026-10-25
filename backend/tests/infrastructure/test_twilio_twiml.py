from infrastructure.services.twilio_call_service import TwilioCallService


def test_call_sends_a_listen_copy_and_connects_laia(settings):
    settings.LAIA = {**settings.LAIA, "PUBLIC_URL": "https://laia.example", "TWILIO_FROM_NUMBER": "+34900000000"}
    twiml = TwilioCallService().call_twiml("o1", "s3cr3t")
    assert '<Start><Stream track="both_tracks" url="wss://laia.example/ws/listen">' in twiml
    assert '<Connect><Stream url="wss://laia.example/ws">' in twiml
    assert twiml.count('<Parameter name="secret" value="s3cr3t" />') == 2


def test_transfer_warns_the_business_in_its_language_and_dials_you(settings):
    settings.LAIA = {**settings.LAIA, "TWILIO_FROM_NUMBER": "+34900000000"}
    twiml = TwilioCallService().transfer_twiml("+34600111222", "Einen Moment, bitte.", "de")
    assert '<Say language="de-DE">Einen Moment, bitte.</Say>' in twiml
    assert '<Dial callerId="+34900000000" timeout="30"><Number>+34600111222</Number></Dial>' in twiml
