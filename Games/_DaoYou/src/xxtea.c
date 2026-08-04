void __fastcall sub_9276F0(__int64 a1, __int64 a2, __int64 a3)
{
  __int64 v5; // x0
  __int64 Instance; // x0
  cocos2d::FileUtils *v7; // x0
  __int64 InstanceEv; // x0
  int n2102531; // w8
  __int64 BytesEv; // x20
  int SizeEv; // w0
  char *p_1; // x2
  unsigned int n0xF_1; // w3
  unsigned int *p_2; // x20
  void *Bytes_1; // x21
  __int64 v16; // x0
  __int64 v17; // x0
  __int64 Bytes; // x20
  int Size; // w0
  char *p; // x2
  unsigned int n0xF; // w3
  __int64 Bytes_3; // x20
  __int64 v23; // x0
  unsigned __int8 *BytesEv_1; // x20
  unsigned int SizeEv_1; // w1
  char *p_3; // x2
  unsigned int n0xF_2; // w3
  __int64 v28; // x0
  void *Bytes_2; // x0
  __int64 v30; // x0
  _QWORD *v31; // x0
  _QWORD *exception; // x0
  _QWORD *v33; // x0
  _QWORD *v34; // x0
  _QWORD *v35; // x0
  unsigned int v36[4]; // [xsp+8h] [xbp-C8h] BYREF
  void *v37; // [xsp+18h] [xbp-B8h]
  __int128 v38; // [xsp+20h] [xbp-B0h] BYREF
  void *v39; // [xsp+30h] [xbp-A0h]
  _BYTE v40[16]; // [xsp+40h] [xbp-90h] BYREF
  size_t v41; // [xsp+50h] [xbp-80h] BYREF
  void *Bytes_5; // [xsp+58h] [xbp-78h] BYREF
  __int64 v43; // [xsp+60h] [xbp-70h] BYREF
  __int64 v44; // [xsp+68h] [xbp-68h] BYREF
  __int64 v45; // [xsp+70h] [xbp-60h] BYREF
  __int64 Bytes_4; // [xsp+78h] [xbp-58h] BYREF
  __int64 v47; // [xsp+80h] [xbp-50h] BYREF
  __int64 Bytes_6; // [xsp+88h] [xbp-48h] BYREF
  size_t v49[2]; // [xsp+90h] [xbp-40h] BYREF

  v49[1] = *(_QWORD *)(_ReadStatusReg(TPIDR_EL0) + 40);
  cocos2d::Data::Data((cocos2d::Data *)v40);
  sub_927B98(v36, a2);
  v5 = std::string::append((int)v36, ".jsc", 4u);
  v39 = *(void **)(v5 + 16);
  v38 = *(_OWORD *)v5;
  *(_QWORD *)(v5 + 8) = 0;
  *(_QWORD *)(v5 + 16) = 0;
  *(_QWORD *)v5 = 0;
  if ( (v36[0] & 1) != 0 )
    operator delete(v37);
  Instance = cocos2d::FileUtils::getInstance((cocos2d::FileUtils *)v5);
  v7 = (cocos2d::FileUtils *)(*(__int64 (__fastcall **)(__int64, __int128 *))(*(_QWORD *)Instance + 200LL))(
                               Instance,
                               &v38);
  if ( ((unsigned __int8)v7 & 1) != 0 )
  {
    InstanceEv = cocos2d::FileUtils::getInstance(v7);
    (*(void (__fastcall **)(unsigned int *__return_ptr, __int64, __int128 *))(*(_QWORD *)InstanceEv + 32LL))(
      v36,
      InstanceEv,
      &v38);
    cocos2d::Data::operator=(v40, v36);
    cocos2d::Data::~Data((cocos2d::Data *)v36);
    n2102531 = *(_DWORD *)cocos2d::Data::getBytes((cocos2d::Data *)v40);
    if ( n2102531 == 2102532 )
    {
      *(_QWORD *)v36 = 0;
      Bytes = cocos2d::Data::getBytes((cocos2d::Data *)v40);
      Size = cocos2d::Data::getSize((cocos2d::Data *)v40);
      if ( (obj_ & 1) != 0 )
        p = (char *)p;
      else
        p = (char *)&obj_ + 1;
      if ( (obj_ & 1) != 0 )
        n0xF = DWORD2(obj_);
      else
        n0xF = (unsigned __int64)(unsigned __int8)obj_ >> 1;
      Bytes_3 = xxtea_decrypt((unsigned __int8 *)(Bytes + 4), Size - 4, p, n0xF, v36);
      v45 = *(_QWORD *)v36;
      Bytes_4 = Bytes_3;
      v23 = *(_QWORD *)(a3 + 32);
      if ( !v23 )
      {
        exception = __cxa_allocate_exception(8u);
        *exception = off_1F9F498;
        __cxa_throw(
          exception,
          (struct type_info *)&`typeinfo for'std::bad_function_call,
          (void (*)(void *))&std::exception::~exception);
      }
      (*(void (__fastcall **)(__int64, __int64 *, __int64 *))(*(_QWORD *)v23 + 48LL))(v23, &Bytes_4, &v45);
    }
    else
    {
      if ( n2102531 == 2102531 )
      {
        *(_QWORD *)v36 = 0;
        BytesEv = cocos2d::Data::getBytes((cocos2d::Data *)v40);
        SizeEv = cocos2d::Data::getSize((cocos2d::Data *)v40);
        if ( (obj_ & 1) != 0 )
          p_1 = (char *)p;
        else
          p_1 = (char *)&obj_ + 1;
        if ( (obj_ & 1) != 0 )
          n0xF_1 = DWORD2(obj_);
        else
          n0xF_1 = (unsigned __int64)(unsigned __int8)obj_ >> 1;
        p_2 = (unsigned int *)xxtea_decrypt((unsigned __int8 *)(BytesEv + 4), SizeEv - 4, p_1, n0xF_1, v36);
        v49[0] = *p_2;
        Bytes_1 = malloc(v49[0]);
        if ( (unsigned int)uncompress(Bytes_1, v49, p_2 + 1, *(_QWORD *)v36 - 4LL) )
        {
          v43 = 0;
          v44 = 0;
          v16 = *(_QWORD *)(a3 + 32);
          if ( !v16 )
          {
            v34 = __cxa_allocate_exception(8u);
            *v34 = off_1F9F498;
            __cxa_throw(
              v34,
              (struct type_info *)&`typeinfo for'std::bad_function_call,
              (void (*)(void *))&std::exception::~exception);
          }
          (*(void (__fastcall **)(__int64, __int64 *, __int64 *))(*(_QWORD *)v16 + 48LL))(v16, &v44, &v43);
        }
        else
        {
          v41 = v49[0];
          Bytes_5 = Bytes_1;
          v30 = *(_QWORD *)(a3 + 32);
          if ( !v30 )
          {
            v35 = __cxa_allocate_exception(8u);
            *v35 = off_1F9F498;
            __cxa_throw(
              v35,
              (struct type_info *)&`typeinfo for'std::bad_function_call,
              (void (*)(void *))&std::exception::~exception);
          }
          (*(void (__fastcall **)(__int64, void **, size_t *))(*(_QWORD *)v30 + 48LL))(v30, &Bytes_5, &v41);
        }
        free(p_2);
        Bytes_2 = Bytes_1;
LABEL_39:
        free(Bytes_2);
        if ( (v38 & 1) == 0 )
          goto LABEL_18;
        goto LABEL_17;
      }
      *(_QWORD *)v36 = 0;
      BytesEv_1 = (unsigned __int8 *)cocos2d::Data::getBytes((cocos2d::Data *)v40);
      SizeEv_1 = cocos2d::Data::getSize((cocos2d::Data *)v40);
      if ( (obj_ & 1) != 0 )
        p_3 = (char *)p;
      else
        p_3 = (char *)&obj_ + 1;
      if ( (obj_ & 1) != 0 )
        n0xF_2 = DWORD2(obj_);
      else
        n0xF_2 = (unsigned __int64)(unsigned __int8)obj_ >> 1;
      Bytes_3 = xxtea_decrypt(BytesEv_1, SizeEv_1, p_3, n0xF_2, v36);
      v47 = *(_QWORD *)v36;
      Bytes_6 = Bytes_3;
      v28 = *(_QWORD *)(a3 + 32);
      if ( !v28 )
      {
        v33 = __cxa_allocate_exception(8u);
        *v33 = off_1F9F498;
        __cxa_throw(
          v33,
          (struct type_info *)&`typeinfo for'std::bad_function_call,
          (void (*)(void *))&std::exception::~exception);
      }
      (*(void (__fastcall **)(__int64, __int64 *, __int64 *))(*(_QWORD *)v28 + 48LL))(v28, &Bytes_6, &v47);
    }
    Bytes_2 = (void *)Bytes_3;
    goto LABEL_39;
  }
  *(_QWORD *)v36 = 0;
  v49[0] = 0;
  v17 = *(_QWORD *)(a3 + 32);
  if ( !v17 )
  {
    v31 = __cxa_allocate_exception(8u);
    *v31 = off_1F9F498;
    __cxa_throw(
      v31,
      (struct type_info *)&`typeinfo for'std::bad_function_call,
      (void (*)(void *))&std::exception::~exception);
  }
  (*(void (__fastcall **)(__int64, unsigned int *, size_t *))(*(_QWORD *)v17 + 48LL))(v17, v36, v49);
  if ( (v38 & 1) != 0 )
LABEL_17:
    operator delete(v39);
LABEL_18:
  cocos2d::Data::~Data((cocos2d::Data *)v40);
}