from verification.verification import VerificationManager
from verification.magic import Magic

def register(register_xslt_function, register_qwebchannel_class, register_proteus_component, register_export_strategy):
    register_qwebchannel_class("verificationManager", VerificationManager)

    # register_proteus_component("magic", Magic)