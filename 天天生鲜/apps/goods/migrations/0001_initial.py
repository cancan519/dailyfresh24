# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Goods',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('name', models.CharField(verbose_name='名称', max_length=100)),
                ('desc', tinymce.models.HTMLField(blank=True, verbose_name='详细介绍', default='')),
            ],
            options={
                'verbose_name_plural': '商品',
                'verbose_name': '商品',
                'db_table': 'df_goods',
            },
        ),
        migrations.CreateModel(
            name='GoodsCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('name', models.CharField(verbose_name='名称', max_length=20)),
                ('logo', models.CharField(verbose_name='标识', max_length=100)),
                ('image', models.ImageField(upload_to='category', verbose_name='图片')),
            ],
            options={
                'verbose_name_plural': '商品类别',
                'verbose_name': '商品类别',
                'db_table': 'df_goods_category',
            },
        ),
        migrations.CreateModel(
            name='GoodsImage',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('image', models.ImageField(upload_to='goods', verbose_name='图片')),
            ],
            options={
                'verbose_name_plural': '商品图片',
                'verbose_name': '商品图片',
                'db_table': 'df_goods_image',
            },
        ),
        migrations.CreateModel(
            name='GoodsSKU',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('name', models.CharField(verbose_name='名称', max_length=100)),
                ('title', models.CharField(verbose_name='简介', max_length=200)),
                ('unit', models.CharField(verbose_name='销售单位', max_length=10)),
                ('price', models.DecimalField(verbose_name='价格', max_digits=10, decimal_places=2)),
                ('stock', models.IntegerField(verbose_name='库存', default=0)),
                ('sales', models.IntegerField(verbose_name='销量', default=0)),
                ('default_image', models.ImageField(upload_to='goods', verbose_name='图片')),
                ('status', models.BooleanField(verbose_name='是否上线', default=True)),
                ('category', models.ForeignKey(to='goods.GoodsCategory', verbose_name='类别')),
                ('goods', models.ForeignKey(to='goods.Goods', verbose_name='商品')),
            ],
            options={
                'verbose_name_plural': '商品SKU',
                'verbose_name': '商品SKU',
                'db_table': 'df_goods_sku',
            },
        ),
        migrations.CreateModel(
            name='IndexCategoryGoodsBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('display_type', models.SmallIntegerField(choices=[(0, '标题'), (1, '图片')], verbose_name='展示类型')),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
                ('category', models.ForeignKey(to='goods.GoodsCategory', verbose_name='商品类别')),
                ('sku', models.ForeignKey(to='goods.GoodsSKU', verbose_name='商品SKU')),
            ],
            options={
                'verbose_name_plural': '主页分类展示商品',
                'verbose_name': '主页分类展示商品',
                'db_table': 'df_index_category_goods',
            },
        ),
        migrations.CreateModel(
            name='IndexGoodsBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('image', models.ImageField(upload_to='banner', verbose_name='图片')),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
                ('sku', models.ForeignKey(to='goods.GoodsSKU', verbose_name='商品SKU')),
            ],
            options={
                'verbose_name_plural': '主页轮播商品',
                'verbose_name': '主页轮播商品',
                'db_table': 'df_index_goods',
            },
        ),
        migrations.CreateModel(
            name='IndexPromotionBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('name', models.CharField(verbose_name='活动名称', max_length=50)),
                ('url', models.URLField(verbose_name='活动连接')),
                ('image', models.ImageField(upload_to='banner', verbose_name='图片')),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
            ],
            options={
                'verbose_name_plural': '主页促销活动',
                'verbose_name': '主页促销活动',
                'db_table': 'df_index_promotion',
            },
        ),
        migrations.AddField(
            model_name='goodsimage',
            name='sku',
            field=models.ForeignKey(to='goods.GoodsSKU', verbose_name='商品SKU'),
        ),
    ]
