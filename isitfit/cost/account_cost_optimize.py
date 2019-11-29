def pipeline_factory(mm_eco, mm_rco, ctx):
    # configure tqdm
    from isitfit.tqdmman import TqdmL2Quiet, TqdmL2Verbose
    tqdml2_ec2 = TqdmL2Verbose(ctx)
    tqdml2_redshift = TqdmL2Verbose(ctx)
    tqdml2_account = TqdmL2Quiet(ctx)

    # start download data and processing
    it_l = [
      (mm_eco, tqdml2_ec2,      "EC2"     ),
      (mm_rco, tqdml2_redshift, "Redshift"),
    ]
    it_w = tqdml2_account(it_l, total=len(it_l), desc="AWS EC2, Redshift cost optimize")
    for mm_i, tqdml2_i, desc_i in it_w:
      logger.info("Fetching history: %s..."%desc_i)
      mm_i.get_ifi(tqdml2_i)

