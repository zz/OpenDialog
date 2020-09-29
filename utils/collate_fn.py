from header import *

def dialog_collate_fn(batch):
    pad = 0
    cid, cid_l, rid, rid_l = [], [], [], []
    for i in batch:
        cid.append(i[0])
        cid_l.append(i[1])
        rid.append(i[2])
        rid_l.append(i[3])
    cid = pad_sequence(cid, batch_first=False, padding_value=pad)
    rid = pad_sequence(rid, batch_first=False, padding_value=pad)
    cid_l = torch.LongTensor(cid_l)
    rid_l = torch.LongTensor(rid_l)
    if torch.cuda.is_available():
        cid = cid.cuda()
        rid = rid.cuda()
        cid_l = cid_l.cuda()
        rid_l = rid_l.cuda()
    return cid, cid_l, rid, rid_l

def nli_collate_fn(batch):
    pad = 0
    sid, label = [], []
    for i in batch:
        sid.append(i['sid'])
        label.append(i['label'])
    sid = pad_sequence(sid, batch_first=True, padding_value=pad)    # [batch, seq]
    label = torch.LongTensor(label)    # [batch]
    if torch.cuda.is_available():
        sid, label = sid.cuda(), label.cuda()
    return sid, label

def gpt2_lm_collate_fn(batch):
    pad = 0
    batch = [i['context_id'] for i in batch]
    # NOTE:
    random.shuffle(batch)
    ids = pad_sequence(batch, batch_first=True, padding_value=pad)
    if torch.cuda.is_available():
        ids = ids.cuda()
    return ids

def gpt2retrieval_train_collate_fn(batch):
    '''
    GPT2Dataset -> gpt2retrieval_train_collate_fn
    '''
    pad = 0
    candidates_k = len(batch[0]['retrieval_embedding'])
    ctx, ir_ctx = [], []
    for i in batch:
        ctx.append(i['context_id'])
        ir_ctx.append(i['retrieval_embedding'])
    ctx = pad_sequence(ctx, batch_first=True, padding_value=pad)    # [batch, seq]
    ir_embed = []    # k*[batch, 300]
    for i in range(candidates_k):
        item_ = torch.tensor([item[i] for item in ir_ctx])    # [batch, 300]
        ir_embed.append(item_)
    ir_embed = torch.stack(ir_embed).mean(dim=0)    # [batch, 300]
    if torch.cuda.is_available():
        ir_embed = ir_embed.cuda()
        ctx = ctx.cuda()
    return ir_embed, ctx

def gpt2retrieval_test_collate_fn(batch):
    '''
    batch must be 1
    '''
    pad = 0
    candidates_k = len(batch[0]['retrieval_embedding'])
    assert len(batch) == 1, f'[!] batch must be 1, but got {len(batch)}'
    ir_embed_, ctx, res = batch[0]['retrieval_embedding'], batch[0]['context_id'], batch[0]['reply_id']
    ir_embed = []
    for i in ir_embed_:
        i = torch.tensor(i)    # [300]
        ir_embed.append(i)
    ir_embed = torch.stack(ir_embed).mean(dim=0)    # [300]
    # ctx/res: [batch, max_len]
    if torch.cuda.is_available():
        ir_embed = ir_embed.cuda()
        ctx, res = ctx.cuda(), res.cuda()
    # 300; seq; seq
    return ir_embed, ctx, res

def gpt2_test_collate_fn_batch(batch):
    pad = 0
    ctx, res = [], []
    for i in batch:
        ctx.append(i['context_id'])
        res.append(i['reply_id'])
    ctx = pad_sequence(ctx, batch_first=True, padding_value=pad)
    res = pad_sequence(res, batch_first=True, padding_value=pad)
    if torch.cuda.is_available():
        ctx = ctx.cuda()
        res = res.cuda()
    return ctx, res

def multigpt2_train_collate_fn(batch):
    '''
    bundle['context_text']
    bundle['context_id']
    bundle['retrieval_list_text']
    bundle['retrieval_list']

    return:
    1. context_id: [batch, seq]
    2. retrieval_list_id: [[batch, seq], [batch, seq], ...]
    '''
    pad = 0
    retrieval_samples = len(batch[0]['retrieval_list'])
    ctx = []
    for i in batch:
        ctx.append(i['context_id'])
    retrieval_list = []
    for idx in range(retrieval_samples):
        r_ = []
        for i in batch:
            r_.append(i['retrieval_list'][idx])
        retrieval_list.append(r_)
    ctx = pad_sequence(ctx, batch_first=True, padding_value=pad)
    r_list = []
    for i in retrieval_list:
        i = pad_sequence(i, batch_first=True, padding_value=pad)
        if torch.cuda.is_available():
            i = i.cuda()
        r_list.append(i)
    if torch.cuda.is_available():
        ctx = ctx.cuda()
    return ctx, r_list

def multigpt2_test_collate_fn(batch):
    '''
    In order to avoid the pad value of the src, batch must be 1
    '''
    pad = 0
    assert len(batch) == 1, f'[!] batch size must be 1, but got {len(batch)}'
    ctx, res_ = batch[0]['context_id'], batch[0]['retrieval_list']
    res = batch[0]['reply_id']
    if torch.cuda.is_available():
        ctx = ctx.cuda()
        res = res.cuda()
        r_ = []
        for i in res_:
            r_.append(i.cuda())
    return ctx, res, r_

def bert_ir_mc_collate_fn(batch):
    '''input: B*N*S, return: [B, N, S]
    for test mode: N=10; for train mode: N=2
    '''
    ctx_, label = [], []    # [B*N], [B]
    N = len(batch[0]['ids'])
    for i in batch:
        label.append(i['label'])
        ctx_.append([torch.LongTensor(k) for k in i['ids']])
    
    # shuffle the samples in the batch
    random_idx = list(range(len(ctx_)))
    random.shuffle(random_idx)
    ctx = []
    for i in random_idx:
        ctx.extend(ctx_[i])
    label = [label[i] for i in random_idx]
    
    ctx = pad_sequence(ctx, batch_first=True, padding_value=0)    # [B*N, S]
    ctx = torch.stack(ctx.split(N))    # [B, N, S]
    label = torch.tensor(label, dtype=torch.long)    # [B]
    if torch.cuda.is_available():
        ctx, label = ctx.cuda(), label.cuda()
    return ctx, label

def bert_ir_mc_test_collate_fn(batch):
    '''input: B*N*S, return: [B, N, S]
    for test mode: N=10; for train mode: N=2
    '''
    ctx = []    # [B*N], [B]
    for i in batch:
        ctx.extend(i)
    ctx = pad_sequence(ctx, batch_first=True, padding_value=0)    # [B*N, S]
    ctx = torch.stack(ctx.split(10))    # [B, N, S]
    if torch.cuda.is_available():
        ctx = ctx.cuda()
    return ctx

def bert_ir_dis_train_collate_fn(batch):
    pad = 0
    cxt, label = [], []
    for i in batch:
        cxt.append(torch.LongTensor(i['context_id']))
        label.append(i['label'])
    random_idx = list(range(len(cxt)))
    random.shuffle(random_idx)
    cxt = pad_sequence(cxt, batch_first=True, padding_value=pad)    # [batch, seq]
    cxt = cxt[random_idx]

    label = torch.tensor(label, dtype=torch.long)    # [batch]
    label = label[random_idx]
    if torch.cuda.is_available():
        cxt, label = cxt.cuda(), label.cuda()
    return cxt, label

def bert_ir_train_collate_fn(batch):
    pad = 0
    cxt, token_type_ids, label = [], [], []
    for i in batch:
        cxt.append(i[0])
        token_type_ids.append(i[1])
        label.append(i[2])
    # shuffle
    random_idx = list(range(len(cxt)))
    random.shuffle(random_idx)
    cxt = pad_sequence(cxt, batch_first=True, padding_value=pad)    # [batch, seq]
    token_type_ids = pad_sequence(token_type_ids, batch_first=True, padding_value=pad)
    cxt = cxt[random_idx]
    token_type_ids = token_type_ids[random_idx]
    label = torch.tensor(label, dtype=torch.long)    # [batch]
    label = label[random_idx]
    
    if torch.cuda.is_available():
        cxt, token_type_ids, label = cxt.cuda(), token_type_ids.cuda(), label.cuda()
    return cxt, token_type_ids, label

def bert_ir_test_collate_fn(batch):
    pad = 0
    cxt, label = [], []
    for i in batch:
        cxt.extend(i[0])
        label.extend(i[1])
    cxt = pad_sequence(cxt, batch_first=True, padding_value=pad)    # [10*batch, seq]
    label = torch.tensor(label, dtype=torch.long)    # [10*batch]
    if torch.cuda.is_available():
        cxt, label = cxt.cuda(), label.cuda()
    return cxt, label

def pone_test_collate_fn(batch):
    ctx, res, a = [], [], []
    for i in batch:
        ctx.append(i[0])
        a.append(i[1])    # [data_size, 3 annotators, 4 scores]
    cxt = pad_sequence(ctx, batch_first=True, padding_value=0)
    if torch.cuda.is_available():
        cxt = cxt.cuda()
    return cxt, a

def pone_train_collate_fn(batch):
    pad = 0
    cxt, res, label = [], [], []
    for i in batch:
        cxt.append(i[0])
        label.append(i[1])
    cxt = pad_sequence(cxt, batch_first=True, padding_value=pad)    # [batch, seq]

    label = torch.tensor(label, dtype=torch.long)    # [batch]
    if torch.cuda.is_available():
        cxt, label = cxt.cuda(), label.cuda()
    return cxt, label
