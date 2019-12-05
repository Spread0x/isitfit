import pandas as pd

from isitfit.utils import logger


class TagsImplierHelper:
  def __init__(self, names_df):
    self.names_df = names_df
    self.names_original = names_df.Name.tolist()

  def freq_list(self):
    logger.info("Step 1: calculate word frequencies")
    # lower-case
    self.names_lower = [x.lower() for x in self.names_original]

    # count single word frequencies
    # https://programminghistorian.org/en/lessons/counting-frequencies
    import re
    #names_split = (' '.join(names_original)).split(' ')
    #words = re.findall("\w+", "the quick person did not realize his speed and the quick person bumped")
    names_split = re.findall("\w+", ' '.join(self.names_lower))

    # Counting bigrams
    # https://stackoverflow.com/a/12488794/4126114
    from itertools import tee, islice
    from collections import Counter
    def ngrams(lst, n):
      tlst = lst
      while True:
        a, b = tee(tlst)
        l = tuple(islice(a, n))
        if len(l) == n:
          yield l
          next(b)
          tlst = b
        else:
          break

    def get_freq(n):
      # names_freq = dict(Counter(zip(names_split, islice(names_split, n-1, None))))
      names_freq = dict(Counter(ngrams(names_split, n)))
      names_freq = [(k,v) for k,v in names_freq.items()]
      return names_freq

    self.freq_1w = get_freq(1)
    self.freq_2w = get_freq(2)

  def freq_df(self):
    logger.info("Step 2: convert word frequencies to pandas dataframe")

    # convert to pandas dataframe
    
    def min_is_2(df_in):
      return df_in[df_in.n >= 2] # minimum occurence is 2
    
    def freq2df(freq_in, l):
      df_freq_in = pd.DataFrame(freq_in, columns=['word_tuple', 'n'])
      df_freq_in = min_is_2(df_freq_in)
      df_freq_in['l'] = l
      return df_freq_in
    
    df_freq_1w = freq2df(self.freq_1w, 1)
    df_freq_1w['word_1'] = df_freq_1w.word_tuple.apply(lambda x: x[0])
    df_freq_1w['word_2'] = None
    df_freq_2w = freq2df(self.freq_2w, 2)
    df_freq_2w['word_1'] = df_freq_2w.word_tuple.apply(lambda x: x[0])
    df_freq_2w['word_2'] = df_freq_2w.word_tuple.apply(lambda x: x[1])
    
    # print("##########")
    # print("before filter")
    # print("1w")
    # print(df_freq_1w)
    # print("")
    # print("2w")
    # print(df_freq_2w)
    # print("##########")
    
    
    # filter out 1-grams if their 2-gram counterpart is superior
    df_freq_2w = df_freq_2w.merge(df_freq_1w[['word_1', 'n']], how='left', left_on='word_1', right_on='word_1', suffixes=['', '.1w=2w.word1'])
    df_freq_2w = df_freq_2w.merge(df_freq_1w[['word_1', 'n']], how='left', left_on='word_2', right_on='word_1', suffixes=['', '.1w=2w.word2'])
    df_freq_2w = df_freq_2w.drop(columns=['word_1.1w=2w.word2'])
    df_freq_2w = df_freq_2w[(df_freq_2w.n >= df_freq_2w['n.1w=2w.word1']) & (df_freq_2w.n >= df_freq_2w['n.1w=2w.word2'])]
    
    # print("")
    # print("after filtering 2w")
    # print(df_freq_2w)
    
    # drop from 1w the components that were used in the 2w
    df_freq_1w = df_freq_1w[~(df_freq_1w.word_1.isin(df_freq_2w.word_1) | df_freq_1w.word_1.isin(df_freq_2w.word_2))]
    
    # drop columns
    df_freq_2w = df_freq_2w.drop(columns=['n.1w=2w.word1', 'n.1w=2w.word2'])
    
    # concatenate into 1 df
    df_freq_all = pd.concat([df_freq_1w,df_freq_2w], axis=0)
    df_freq_all['word_combined'] = df_freq_all.apply(lambda r: r.word_1 if r.word_2 is None else r.word_1 + ' ' + r.word_2, axis=1)
    
    #print("")
    #print("final df")
    #print(df_freq_all)
    self.df_freq_all = df_freq_all

  def tag_set(self):
    logger.info("Step 3: Generate a set of tags")

    # merge with original names
    df_ori = pd.DataFrame({'original': self.names_original, 'lower': self.names_lower, 'instance_id': self.names_df.instance_id})
    df_ori['tag_set'] = None
    
    import re
    def myfind(t, n):
      # https://stackoverflow.com/a/48205793/4126114
      f = re.findall(r"\b%s\b"%t, n, re.IGNORECASE)
      return len(f)>0

    self.len_ori = df_ori.shape[0]
    for i in range(self.len_ori):
      name_value = df_ori.iloc[i].lower
      for j in range(self.df_freq_all.shape[0]):
        i_sub = [myfind(tag_value, name_value) for tag_value in self.df_freq_all.word_combined.values]
        df_sub = self.df_freq_all[i_sub]
        df_sub = df_sub.sort_values('n', ascending=False)
        df_sub = df_sub.iloc[:3]
        df_ori.at[i, 'tag_set'] = set(df_sub.word_combined.values)
    
    self.df_ori = df_ori

  def tag_list(self):
    logger.info("Step 4: convert the set of tags to a list of tags")

    df_ori = self.df_ori

    # initialize
    # just doing [[None]*3]*len_ori doesn't work
    df_ori['tag_list'] = None
    for i1 in range(self.len_ori):
      df_ori.at[i1, 'tag_list'] = [None]*3
    
    # distributing the tag_set to tag_1, tag_2, tag_3 in such a way that for example "app" is at tag_1 for all the instances
    tag_processed = set()
    for i1 in range(self.len_ori):
      for tag_value in df_ori.iloc[i1].tag_set:
        if tag_value in tag_processed:
          continue
    
        tag_processed.add(tag_value)
        logger.debug("<<<<<<<<>>>>>>>>>>>>")
        logger.debug("%i: %s"%(i1, tag_value))
        logger.debug(df_ori)
    
        if tag_value in df_ori.at[i1, 'tag_list']:
          continue # already inserted this tag
    
        # find free indeces in current list
        if None not in df_ori.at[i1, 'tag_list']:
          raise Exception("No more space in list for %s"%tag_value)
    
        # https://stackoverflow.com/a/6294205/4126114
        free_indices = [i for i, x in enumerate(df_ori.at[i1, 'tag_list']) if x is None]

        # find the first free index which is ok for all entries having this tag
        free_chosen = None
        logger.debug("Searching for free index for %s"%tag_value)
        for free_i1 in free_indices:
          found_conflict = False
          for i2 in range(self.len_ori):
            if found_conflict: break
            if i2 <= i1: continue
            logger.debug("Checking row %i"%i2)
            # if tag in set of tags for this 2nd row
            if tag_value in df_ori.loc[i2].tag_set:
              # and if the value for this tag is not *already* set
              if tag_value not in df_ori.loc[i2].tag_list:
                if df_ori.loc[i2, 'tag_list'][free_i1] is not None:
                  logger.debug("Found conflict")
                  found_conflict = True

          if not found_conflict:
            logger.debug("Found chosen free index at %i"%free_i1)
            free_chosen = free_i1
            break

        # if no free index chosen, raise Exception
        if free_chosen is None:
          raise Exception("Conflict found: %s didn't find a free index to use"%(tag_value))

        # otherwise use the chosen index
        # Old way of getting first None only # free_chosen = df_ori.at[i1, 'tag_list'].index(None)
        free_chosen = free_i1
        df_ori.at[i1, 'tag_list'][free_chosen] = tag_value
    
        # set this tag for all other rows at "free_chosen"
        for i2 in range(self.len_ori):
          if i2 <= i1: continue
          if tag_value in df_ori.loc[i2].tag_set:
            if tag_value not in df_ori.loc[i2].tag_list:
              if df_ori.loc[i2, 'tag_list'][free_chosen] is not None:
                raise Exception("Conflict found despite pre-check? %s wants to be at %i but found %s already"%(tag_value, free_chosen, df_ori.loc[i2, 'tag_list'][free_chosen]))
    
            df_ori.at[i2, 'tag_list'][free_chosen] = tag_value
    
    # mesh out the tag_list to tag_1 tag_2 tag_3
    df_ori['tag_1'] = df_ori.tag_list.apply(lambda x: x[1-1])
    df_ori['tag_2'] = df_ori.tag_list.apply(lambda x: x[2-1])
    df_ori['tag_3'] = df_ori.tag_list.apply(lambda x: x[3-1])

    # re-order columns
    df_ori = df_ori.rename(columns={'original': 'instance_name'})
    df_ori = df_ori[['instance_id', 'instance_name', 'tag_1', 'tag_2', 'tag_3']]
    
    # done
    #print("")
    #print("tagged")
    #print(df_ori)

    self.df_ori = df_ori

#------------------------

class TagsImplierMain:

  def __init__(self, names_original):
    self.helper = TagsImplierHelper(names_original)

  def imply(self):
    self.helper.freq_list()
    self.helper.freq_df()
    self.helper.tag_set()
    self.helper.tag_list()
    return self.helper.df_ori

#------------------------

if __name__=='__main__':
    names_original = [
      'cool php app for accounting',
      'weird app for BUSINESS',
      'a crm portal for accounting',
      'crm portal for business',
    ]
    
    #tags_expected = [
    #  ['app', 'accounting', 'for'],
    #  ['app', 'business',   'for'],
    #  ['crm portal', 'accounting', 'for'],
    #  ['crm portal', 'business',   'for'],
    #]
    
    tags_implier = TagsImplierMain(names_original)
    df_tagged = tags_implier.imply()
    print(df_tagged)
