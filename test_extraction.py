from data import DataValidator, extract_customers

# Extract data
df = extract_customers(limit=100)
print(f"✅ Extracted {len(df)} customers\n")

# Validate
validator = DataValidator()
result = validator.validate(df)

print(f"Validation: {'PASSED ✅' if result.passed else 'FAILED ❌'}")
print(f"Quality Score: {validator.get_data_quality_score(df):.1f}/100")
print(f"Total checks: {result.total_checks}")
print(f"Failed checks: {result.failed_checks}\n")

if result.errors:
    print("❌ Errors:")
    for error in result.errors:
        print(f"  - {error['rule']}: {error['description']}")
        print(f"    Failed: {error['failed_count']} rows ({error['failed_percentage']:.1f}%)")
    print()

if result.warnings:
    print("⚠️  Warnings:")
    for warning in result.warnings:
        print(f"  - {warning['rule']}: {warning['description']}")
    print()

print("\n📊 Sample data:")
print(df.head())
