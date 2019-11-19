def tagsContain(f_tn, ec2_obj):
  if ec2_obj.tags is None:
    return False
  
  for t in ec2_obj.tags:
    for k in ['Key', 'Value']:
      if f_tn in t[k].lower():
        return True
  
  return False



class Ec2TagFilter:
  def __init__(self, filter_tags):
    self.filter_tags = filter_tags

  def per_ec2(self, context_ec2):
    # if filters requested, check that this instance passes

    # set in context
    context_ec2['filter_tags'] = self.filter_tags

    if self.filter_tags is None:
      # to continue with other listeners
      return context_ec2

    f_tn = self.filter_tags.lower()
    passesFilter = tagsContain(f_tn, context_ec2['ec2_obj'])
    if not passesFilter:
      # break other listeners
      return None

    # otherwise continue
    return context_ec2
