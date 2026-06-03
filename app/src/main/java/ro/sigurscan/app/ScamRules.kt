package ro.sigurscan.app

object ScamRules {
    val TRUSTED_OFFICIAL_DOMAINS: Map<String, List<String>>
        get() = BrandKnowledgeRegistry.trustedOfficialDomains
}
