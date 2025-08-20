"""Test API endpoints."""


class TestProductGroups:
    """Test product group endpoints."""

    async def test_list_product_groups_empty(self, client):
        """Test listing product groups when none exist."""
        response = await client.get("/api/product-groups/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_product_group(self, client):
        """Test creating a product group."""
        data = {"name": "Test Group", "description": "A test group"}
        response = await client.post("/api/product-groups/", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == data["name"]
        assert result["description"] == data["description"]
        assert "id" in result
        assert "created_at" in result

    async def test_create_product_group_duplicate_name(self, client, sample_product_group):
        """Test creating a product group with duplicate name fails."""
        data = {"name": sample_product_group.name, "description": "Another group"}
        response = await client.post("/api/product-groups/", json=data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_get_product_group(self, client, sample_product_group):
        """Test getting a specific product group."""
        response = await client.get(f"/api/product-groups/{sample_product_group.id}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == sample_product_group.id
        assert result["name"] == sample_product_group.name

    async def test_get_product_group_not_found(self, client):
        """Test getting a non-existent product group."""
        response = await client.get("/api/product-groups/999")
        assert response.status_code == 404

    async def test_update_product_group(self, client, sample_product_group):
        """Test updating a product group."""
        data = {"description": "Updated description"}
        response = await client.patch(f"/api/product-groups/{sample_product_group.id}", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["description"] == data["description"]
        assert result["name"] == sample_product_group.name  # Unchanged

    async def test_delete_product_group(self, client, sample_product_group):
        """Test deleting a product group."""
        response = await client.delete(f"/api/product-groups/{sample_product_group.id}")
        assert response.status_code == 200

        # Verify it's deleted
        response = await client.get(f"/api/product-groups/{sample_product_group.id}")
        assert response.status_code == 404


class TestProducts:
    """Test product endpoints."""

    async def test_create_product(self, client, sample_product_group):
        """Test creating a product."""
        data = {
            "name": "Test Product",
            "version": "1.0.0",
            "description": "A test product",
            "product_group_id": sample_product_group.id,
        }
        response = await client.post("/api/products/", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == data["name"]
        assert result["version"] == data["version"]
        assert result["product_group_id"] == data["product_group_id"]

    async def test_create_product_invalid_group(self, client):
        """Test creating a product with invalid group ID."""
        data = {"name": "Test Product", "product_group_id": 999}
        response = await client.post("/api/products/", json=data)
        assert response.status_code == 400

    async def test_list_products_with_filter(self, client, sample_product, sample_product_group):
        """Test listing products filtered by group."""
        response = await client.get(f"/api/products/?product_group_id={sample_product_group.id}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["id"] == sample_product.id

    async def test_get_product(self, client, sample_product):
        """Test getting a specific product."""
        response = await client.get(f"/api/products/{sample_product.id}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == sample_product.id
        assert result["name"] == sample_product.name


class TestVariants:
    """Test variant endpoints."""

    async def test_create_variant(self, client, sample_architecture):
        """Test creating a variant."""
        data = {"name": "Test Variant", "description": "A test variant", "architecture_id": sample_architecture.id}
        response = await client.post("/api/variants/", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == data["name"]
        assert result["architecture_id"] == data["architecture_id"]

    async def test_list_variants_with_filter(self, client, sample_variant, sample_architecture):
        """Test listing variants filtered by architecture."""
        response = await client.get(f"/api/variants/?architecture_id={sample_architecture.id}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["id"] == sample_variant.id


class TestArtifacts:
    """Test artifact endpoints."""

    async def test_create_artifact(self, client, sample_variant):
        """Test creating an artifact."""
        data = {
            "name": "Test Artifact",
            "artifact_type": "base_image",
            "status": "pending",
            "location": "s3://bucket/artifact.img",
            "variant_id": sample_variant.id,
        }
        response = await client.post("/api/artifacts/", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == data["name"]
        assert result["artifact_type"] == data["artifact_type"]
        assert result["status"] == data["status"]
        assert result["variant_id"] == data["variant_id"]

    async def test_list_artifacts_with_filters(self, client, sample_artifact, sample_variant):
        """Test listing artifacts with various filters."""
        # Test variant filter
        response = await client.get(f"/api/artifacts/?variant_id={sample_variant.id}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["id"] == sample_artifact.id

        # Test type filter
        response = await client.get(f"/api/artifacts/?artifact_type={sample_artifact.artifact_type.value}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1

        # Test status filter
        response = await client.get(f"/api/artifacts/?status={sample_artifact.status.value}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1

    async def test_artifact_stats(self, client, sample_artifact):
        """Test artifact statistics endpoint."""
        response = await client.get("/api/artifacts/stats/summary")
        assert response.status_code == 200
        stats = response.json()
        assert "by_status" in stats
        assert "by_type" in stats
        assert "total_size_bytes" in stats
        assert stats["by_status"]["completed"] == 1
        assert stats["by_type"]["base_image"] == 1

    async def test_update_artifact_status(self, client, sample_artifact):
        """Test updating an artifact's status."""
        data = {"status": "failed"}
        response = await client.patch(f"/api/artifacts/{sample_artifact.id}", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "failed"
        assert result["name"] == sample_artifact.name  # Unchanged


class TestHealthCheck:
    """Test health check endpoint."""

    async def test_health_check(self, client):
        """Test the health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
        assert "version" in result


class TestOpenAPISpec:
    """Test OpenAPI specification endpoint."""

    async def test_openapi_spec(self, client):
        """Test that OpenAPI spec is accessible."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert spec["info"]["title"] == "Image Definitions API"
