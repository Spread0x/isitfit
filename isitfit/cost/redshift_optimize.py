from isitfit.utils import logger, taglist2str


from isitfit.cost.redshift_common import CalculatorBaseRedshift
class CalculatorOptimizeRedshift(CalculatorBaseRedshift):

  def per_ec2(self, context_ec2):
      """
      # get all performance dataframes, on the cluster-aggregated level
      """

      # parent
      context_ec2 = super().per_ec2(context_ec2)

      # unpack
      rc_describe_entry = context_ec2['ec2_dict']
      df_single = context_ec2['df_single']

      # build string of taglist
      taglist = rc_describe_entry['Tags']
      taglist = taglist2str(taglist, context_ec2['filter_tags'])

      # summarize into maxmax, maxmin, minmax, minmin
      self.analyze_list.append({
        'Region': rc_describe_entry['Region'],
        'ClusterIdentifier': rc_describe_entry['ClusterIdentifier'],
        'NodeType': rc_describe_entry['NodeType'],
        'NumberOfNodes': rc_describe_entry['NumberOfNodes'],

        'CpuMaxMax': df_single.cpu_used_max.max(),
        #'CpuMaxMin': df_single.cpu_used_max.min(),
        #'CpuMinMax': df_single.cpu_used_min.max(),
        'CpuMinMin': df_single.cpu_used_min.min(),

        'tags': taglist
      })

      # done
      return context_ec2



  def calculate(self, context_all):
    if self.analyze_df.shape[0]==0:
      return context_all

    def classify_cluster_single(row):
        # classify
        if row.CpuMinMin > 70: return "Overused"
        if row.CpuMaxMax <  5: return "Idle"
        if row.CpuMaxMax < 30: return "Underused"
        return "Normal"

    # convert percentages to int since fractions are not very useful
    analyze_df = self.analyze_df

    analyze_df['classification'] = analyze_df.apply(classify_cluster_single, axis=1)

    return context_all




from isitfit.cost.base_reporter import ReporterBase
class ReporterOptimize(ReporterBase):
  def postprocess(self, context_all):
    # unpack
    self.analyzer = context_all['analyzer']
    analyze_df = self.analyzer.analyze_df

    # check if no data
    if analyze_df.shape[0]==0:
      return context_all

    # proceed
    analyze_df['CpuMaxMax'] = analyze_df['CpuMaxMax'].fillna(value=0).astype(int)
    analyze_df['CpuMinMin'] = analyze_df['CpuMinMin'].fillna(value=0).astype(int)

#    # copied from isitfit.cost.optimizationListener.storecsv...
#    # Update 2019-12-17 saving this table to csv is deprecated in favor of cost.account_cost_optimize.ServiceReporter.display2 which saves the data of both ec2 and redshift
#    import tempfile
#    from isitfit.dotMan import DotMan
#    with tempfile.NamedTemporaryFile(prefix='isitfit-full-redshift-', suffix='.csv', delete=False, dir=DotMan().tempdir()) as  csv_fh_final:
#      self.csv_fn_final = csv_fh_final.name
#      import click
#      from termcolor import colored
#      click.echo(colored("Saving final results to %s"%csv_fh_final.name, "cyan"))
#      analyze_df.to_csv(csv_fh_final.name, index=False)
#      click.echo(colored("Save complete", "cyan"))
#
#    # save in context for aggregator
#    context_all['csv_fn_final'] = self.csv_fn_final

    return context_all


# DEPRECATED
#  def display(self, context_all):
#    # copied from isitfit.cost.optimizationListener.display_all
#    analyze_df = self.analyzer.analyze_df
#
#    # display dataframe
#    from isitfit.utils import display_df
#    display_df(
#      "Redshift cluster classifications",
#      analyze_df,
#      self.csv_fn_final,
#      analyze_df.shape,
#      logger
#    )
#    return context_all


  def email(self, context_all):
      # silently return
      # raise Exception("Error emailing optimization: Not yet implemented")
      return context_all




def pipeline_factory(filter_region, ctx, filter_tags):
  # This is a factory method, so it doesn't make sense to display "Analyzing bla" if actually "foo" is analyzed first
  #logger.info("Optimizing redshift clusters")

  from .redshift_common import redshift_cost_core
  ra = CalculatorOptimizeRedshift()
  rr = ReporterOptimize()
  mm = redshift_cost_core(ra, rr, None, filter_region, ctx, filter_tags)

  # listener that was outed in the analyze step by the service aggregator
  # mm.add_listener('all', rr.display)

  return mm
